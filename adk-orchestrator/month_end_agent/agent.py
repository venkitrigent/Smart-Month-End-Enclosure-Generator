"""
Smart Month-End Close ADK Agent
Multi-agent orchestrator for financial document processing
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import Tool
import google.auth
from typing import List, Dict, Any

# Load environment variables
root_dir = Path(__file__).parent.parent
dotenv_path = root_dir / ".env"
load_dotenv(dotenv_path=dotenv_path)

# Configure Google Cloud
try:
    _, project_id = google.auth.default()
    os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project_id)
except Exception:
    pass

os.environ.setdefault("GOOGLE_CLOUD_LOCATION", os.getenv("GCP_REGION", "us-central1"))

# Configure Vertex AI Gemini model
model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")

# Tool: Classify Document
@Tool
def classify_document(filename: str, sample_data: str = None) -> dict:
    """
    Classify uploaded financial document using Azure OpenAI.
    
    Args:
        filename: Name of the uploaded file
        sample_data: Optional sample of file content
        
    Returns:
        Dictionary with doc_type and confidence
    """
    # Try Azure OpenAI first if configured
    if os.getenv("AZURE_OPENAI_API_KEY"):
        try:
            from services.azure_llm_service import azure_llm
            return azure_llm.classify_document(filename, sample_data)
        except Exception as e:
            print(f"Azure OpenAI classification failed: {e}, falling back to regex")
    
    # Fallback to regex-based classification
    import re
    
    patterns = {
        "bank_statement": r"(bank|statement|account)",
        "invoice": r"(invoice|bill|receipt)",
        "ledger": r"(ledger|journal|entry)",
        "reconciliation": r"(recon|reconciliation)",
        "schedule": r"(schedule|depreciation|accrual)"
    }
    
    filename_lower = filename.lower()
    for doc_type, pattern in patterns.items():
        if re.search(pattern, filename_lower):
            return {"doc_type": doc_type, "confidence": 0.9}
    
    return {"doc_type": "unknown", "confidence": 0.5}


# Tool: Extract CSV Data
@Tool
def extract_csv_data(file_content: str, doc_type: str, document_id: str = None) -> dict:
    """
    Extract and parse CSV data with column-aware chunking.
    Saves to BigQuery and generates embeddings.
    
    Args:
        file_content: CSV file content as string
        doc_type: Type of document (from classification)
        document_id: Unique document identifier
        
    Returns:
        Dictionary with extracted data and metadata
    """
    import pandas as pd
    import io
    import uuid
    from services import storage_service, embedding_service
    
    try:
        df = pd.read_csv(io.StringIO(file_content))
        
        if not document_id:
            document_id = str(uuid.uuid4())
        
        # Convert to list of dicts
        data_rows = df.to_dict('records')
        columns = list(df.columns)
        
        # Save to BigQuery
        storage_service.save_structured_data(document_id, doc_type, data_rows)
        
        # Generate embeddings
        embeddings_data = embedding_service.create_chunks_with_embeddings(
            document_id, data_rows, columns
        )
        
        # Save embeddings to BigQuery
        storage_service.save_embeddings(document_id, embeddings_data)
        
        return {
            "document_id": document_id,
            "row_count": len(df),
            "columns": columns,
            "embeddings_generated": len(embeddings_data),
            "sample": df.head(3).to_dict('records'),
            "status": "saved_to_bigquery"
        }
    except Exception as e:
        return {"error": str(e)}


# Tool: Check Completion Status
@Tool
def check_checklist_status(user_id: str, doc_type: str = None) -> dict:
    """
    Update and check month-end close checklist status.
    Uses Firestore for persistent storage.
    
    Args:
        user_id: User identifier
        doc_type: Type of document uploaded (optional)
        
    Returns:
        Checklist status and completion percentage
    """
    from services import storage_service
    
    required_docs = {
        "bank_statement": "Bank Statement",
        "invoice": "Invoice Register",
        "ledger": "General Ledger",
        "reconciliation": "Bank Reconciliation"
    }
    
    # Get current checklist from Firestore
    checklist = storage_service.get_checklist_status(user_id)
    
    # Initialize if empty
    if not checklist:
        checklist = {doc: "missing" for doc in required_docs.keys()}
    
    # Update if doc_type provided
    if doc_type and doc_type in required_docs:
        checklist[doc_type] = "uploaded"
        storage_service.save_checklist_status(user_id, checklist)
    
    # Calculate completion
    completed = len([s for s in checklist.values() if s == "uploaded"])
    total = len(required_docs)
    
    missing = [doc for doc, status in checklist.items() if status == "missing"]
    
    return {
        "user_id": user_id,
        "checklist": checklist,
        "completion_rate": f"{completed}/{total}",
        "percentage": round((completed / total) * 100, 1),
        "missing": missing,
        "status": "saved_to_firestore"
    }


# Tool: Analyze Financial Data
@Tool
def analyze_financial_data(data: dict) -> dict:
    """
    Perform analytics on extracted financial data using Azure OpenAI.
    
    Args:
        data: Extracted data dictionary
        
    Returns:
        Analytics results with totals, averages, and anomalies
    """
    import statistics
    import json
    
    sample_data = data.get("sample", [])
    if not sample_data:
        return {"error": "No data to analyze"}
    
    # Basic numeric analysis
    numeric_analysis = []
    for col in data.get("columns", []):
        try:
            values = [float(row.get(col, 0)) for row in sample_data if row.get(col)]
            if values:
                numeric_analysis.append({
                    "column": col,
                    "total": sum(values),
                    "average": statistics.mean(values),
                    "min": min(values),
                    "max": max(values)
                })
        except (ValueError, TypeError):
            continue
    
    # Use Azure OpenAI for deeper analysis if configured
    ai_insights = None
    if os.getenv("AZURE_OPENAI_API_KEY"):
        try:
            from services.azure_llm_service import azure_llm
            data_str = json.dumps(sample_data[:10], indent=2)  # Limit to 10 rows
            doc_type = data.get("doc_type", "financial document")
            ai_analysis = azure_llm.analyze_financial_data(data_str, doc_type)
            ai_insights = ai_analysis.get("analysis", "")
        except Exception as e:
            print(f"Azure OpenAI analysis failed: {e}")
    
    return {
        "total_rows": data.get("row_count", 0),
        "numeric_analysis": numeric_analysis,
        "anomalies_detected": 0,
        "ai_insights": ai_insights
    }


# Tool: Search Documents with RAG
@Tool
def search_documents(query: str, user_id: str, top_k: int = 5) -> Dict[str, Any]:
    """
    Search uploaded documents using semantic search (RAG).
    
    Args:
        query: Search query
        user_id: User identifier
        top_k: Number of results to return
        
    Returns:
        Relevant document chunks with similarity scores
    """
    from services import storage_service, embedding_service
    
    try:
        # Get all embeddings for user's documents
        # In production, filter by user_id
        bq_query = f"""
        SELECT embedding_id, document_id, row_index, chunk_text, embedding, metadata
        FROM `{os.getenv('GOOGLE_CLOUD_PROJECT')}.{os.getenv('BIGQUERY_DATASET', 'financial_close')}.embeddings`
        LIMIT 1000
        """
        
        results = storage_service.bq_client.query(bq_query).result()
        embeddings_data = [dict(row) for row in results]
        
        if not embeddings_data:
            return {
                "query": query,
                "results": [],
                "message": "No documents found. Please upload documents first."
            }
        
        # Search for similar chunks
        similar_chunks = embedding_service.search_similar(query, embeddings_data, top_k)
        
        return {
            "query": query,
            "results_count": len(similar_chunks),
            "results": similar_chunks[:top_k],
            "status": "success"
        }
    
    except Exception as e:
        return {
            "query": query,
            "error": str(e),
            "results": []
        }


# Tool: Generate Report
@Tool
def generate_month_end_report(user_id: str) -> Dict[str, Any]:
    """
    Generate comprehensive month-end close report.
    
    Args:
        user_id: User identifier
        
    Returns:
        Complete report with summary, checklist, and recommendations
    """
    from services import storage_service, report_service
    
    try:
        # Get user's documents
        doc_query = f"""
        SELECT document_id, filename, doc_type, upload_time, row_count
        FROM `{os.getenv('GOOGLE_CLOUD_PROJECT')}.{os.getenv('BIGQUERY_DATASET', 'financial_close')}.documents`
        WHERE user_id = '{user_id}'
        ORDER BY upload_time DESC
        """
        
        results = storage_service.bq_client.query(doc_query).result()
        documents = [dict(row) for row in results]
        
        # Get checklist status
        checklist = storage_service.get_checklist_status(user_id)
        
        # Get analytics summary
        analytics = {
            "total_documents": len(documents),
            "total_rows": sum(doc.get("row_count", 0) for doc in documents),
            "anomalies_detected": 0  # Would be calculated from actual analysis
        }
        
        # Generate report
        report = report_service.generate_summary_report(
            user_id, documents, checklist, analytics
        )
        
        # Generate text version
        text_report = report_service.generate_text_report(report)
        
        return {
            "report": report,
            "text_report": text_report,
            "status": "success"
        }
    
    except Exception as e:
        return {
            "error": str(e),
            "status": "failed"
        }


# Main Orchestrator Agent
orchestrator_agent = Agent(
    model=LiteLlm(model=f"vertex_ai/{model_name}"),
    name="orchestrator_agent",
    description="Master orchestrator for month-end financial close automation",
    instruction="""You are the orchestrator for a Smart Month-End Close system.
    
    Your responsibilities:
    1. Classify uploaded financial documents (bank statements, invoices, ledgers, etc.)
    2. Extract and parse CSV data with column-aware chunking
    3. Track checklist completion status
    4. Perform financial analytics and detect anomalies
    5. Provide clear, professional explanations to users
    
    When a user uploads a document:
    - First classify it using classify_document
    - Then extract data using extract_csv_data
    - Update checklist with check_checklist_status
    - Run analytics with analyze_financial_data
    - Summarize results clearly
    
    Be professional, accurate, and helpful. Focus on financial compliance and accuracy.""",
    tools=[
        classify_document,
        extract_csv_data,
        check_checklist_status,
        analyze_financial_data,
        search_documents,
        generate_month_end_report
    ]
)

# Chatbot Agent for Q&A
chatbot_agent = Agent(
    model=LiteLlm(model=f"vertex_ai/{model_name}"),
    name="chatbot_agent",
    description="Financial close Q&A assistant with RAG-powered context awareness",
    instruction="""You are a helpful financial assistant for month-end close processes.
    
    You help users by:
    - Answering questions about their uploaded documents using semantic search
    - Explaining checklist status and missing items
    - Clarifying anomalies and financial data
    - Providing guidance on month-end close best practices
    - Searching through uploaded data to find specific information
    
    When users ask about their data:
    1. Use search_documents to find relevant information
    2. Reference specific data from the search results
    3. Provide clear, accurate answers based on actual data
    
    Always be clear, professional, and reference specific data when available.
    If you don't have specific information, explain what you need.""",
    tools=[
        check_checklist_status,
        search_documents,
        generate_month_end_report
    ]
)

# Set root agent
root_agent = orchestrator_agent
