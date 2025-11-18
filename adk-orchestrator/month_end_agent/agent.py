"""
Smart Month-End Close ADK Agent
Multi-agent orchestrator for financial document processing
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
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

# Configure model - Use Azure OpenAI if configured, otherwise Vertex AI
if os.getenv("AZURE_OPENAI_API_KEY"):
    # Azure OpenAI configuration for LiteLLM
    # LiteLLM requires these environment variables to be set
    os.environ["AZURE_API_KEY"] = os.getenv("AZURE_OPENAI_API_KEY")
    os.environ["AZURE_API_BASE"] = os.getenv("AZURE_OPENAI_ENDPOINT")
    os.environ["AZURE_API_VERSION"] = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
    
    deployment_name = os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4o')
    model_name = f"azure/{deployment_name}"
    print(f"✅ Using Azure OpenAI model: {deployment_name}")
    print(f"   Endpoint: {os.getenv('AZURE_OPENAI_ENDPOINT')}")
else:
    # Fallback to Vertex AI Gemini
    gemini_model = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash-exp')
    model_name = f"vertex_ai/{gemini_model}"
    print(f"✅ Using Vertex AI model: {gemini_model}")

# Tool: Classify Document
def classify_document(filename: str, sample_data: str = None) -> dict:
    """
    Classify uploaded financial document type based on filename and content.
    
    This tool analyzes the filename and optional sample data to determine
    the document type (bank_statement, invoice, ledger, reconciliation, etc.).
    
    Args:
        filename: Name of the uploaded file (e.g., "bank_statement_jan.csv")
        sample_data: Optional first few rows of the file content
        
    Returns:
        Dictionary with doc_type (string) and confidence (float 0-1)
        
    Example:
        classify_document("invoice_register.csv") 
        -> {"doc_type": "invoice", "confidence": 0.9}
    """
    import re
    
    # Pattern-based classification (fast and reliable)
    patterns = {
        "bank_statement": r"(bank|statement|account|transaction)",
        "invoice": r"(invoice|bill|receipt)",
        "invoice_register": r"(invoice.*register|register.*invoice)",
        "ledger": r"(ledger|journal|entry|gl)",
        "reconciliation": r"(recon|reconciliation)",
        "trial_balance": r"(trial|balance)",
        "schedule": r"(schedule|depreciation|accrual)"
    }
    
    filename_lower = filename.lower()
    
    # Check patterns in order of specificity
    for doc_type, pattern in patterns.items():
        if re.search(pattern, filename_lower):
            return {
                "doc_type": doc_type,
                "confidence": 0.95,
                "method": "pattern_matching"
            }
    
    # If no pattern matches, try Azure OpenAI for intelligent classification
    if os.getenv("AZURE_OPENAI_API_KEY") and sample_data:
        try:
            from services.azure_llm_service import azure_llm
            result = azure_llm.classify_document(filename, sample_data)
            result["method"] = "azure_openai"
            return result
        except Exception as e:
            print(f"⚠️ Azure OpenAI classification failed: {e}")
    
    # Default fallback
    return {
        "doc_type": "unknown",
        "confidence": 0.5,
        "method": "fallback"
    }


# Tool: Extract CSV Data
def extract_csv_data(file_content: str, doc_type: str, document_id: str = None) -> dict:
    """
    Extract, parse, and store CSV financial data with intelligent processing.
    
    This tool performs complete data pipeline: parsing CSV, saving to BigQuery,
    generating embeddings for RAG search, and validating data quality.
    
    Args:
        file_content: Raw CSV file content as string (with headers)
        doc_type: Document type from classification (e.g., "bank_statement")
        document_id: Unique identifier (auto-generated if not provided)
        
    Returns:
        Dictionary containing:
        - document_id: Unique identifier for this document
        - row_count: Number of data rows processed
        - columns: List of column names
        - embeddings_generated: Number of embedding vectors created
        - sample: First 3 rows as preview
        - status: Processing status
        
    Example:
        extract_csv_data(csv_content, "invoice", "doc-123")
        -> {"document_id": "doc-123", "row_count": 150, "columns": [...], ...}
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
def check_checklist_status(user_id: str, doc_type: str = None) -> dict:
    """
    Check and update month-end close checklist completion status.
    
    This tool tracks which required documents have been uploaded and calculates
    completion percentage. Updates Firestore when new documents are uploaded.
    
    Args:
        user_id: Unique user identifier (required)
        doc_type: Document type to mark as uploaded (optional, e.g., "bank_statement")
        
    Returns:
        Dictionary containing:
        - user_id: User identifier
        - checklist: Dict of {doc_type: status} for all required documents
        - required_docs: Metadata about each document type
        - completion_rate: String like "3/4"
        - percentage: Completion percentage (0-100)
        - missing: List of missing document types
        
    Example:
        check_checklist_status("user123", "invoice")
        -> {"checklist": {"invoice": "uploaded", "ledger": "missing"}, "percentage": 50, ...}
    """
    from services import storage_service
    
    required_docs = {
        "bank_statement": {"name": "Bank Statement", "required": True},
        "invoice": {"name": "Invoice Register", "required": True},
        "invoice_register": {"name": "Invoice Register", "required": True},
        "ledger": {"name": "General Ledger", "required": True},
        "reconciliation": {"name": "Bank Reconciliation", "required": True}
    }
    
    # Get current checklist from Firestore
    checklist = storage_service.get_checklist_status(user_id)
    
    # Initialize if empty
    if not checklist:
        checklist = {doc: "missing" for doc in required_docs.keys()}
    
    # Update if doc_type provided
    if doc_type:
        # Handle invoice_register as invoice
        normalized_type = "invoice" if doc_type == "invoice_register" else doc_type
        if normalized_type in required_docs:
            checklist[normalized_type] = "uploaded"
            # Also update invoice_register if it's invoice
            if normalized_type == "invoice":
                checklist["invoice_register"] = "uploaded"
        storage_service.save_checklist_status(user_id, checklist)
    
    # Calculate completion
    completed = len([s for s in checklist.values() if s == "uploaded"])
    total = len(required_docs)
    
    missing = [doc for doc, status in checklist.items() if status == "missing"]
    
    return {
        "user_id": user_id,
        "checklist": checklist,
        "required_docs": required_docs,
        "completion_rate": f"{completed}/{total}",
        "percentage": round((completed / total) * 100, 1),
        "missing": missing,
        "status": "saved_to_firestore"
    }


# Tool: Analyze Financial Data
def analyze_financial_data(data: dict, doc_type: str = None) -> dict:
    """
    Perform deep analytics on extracted financial data.
    Detects anomalies, calculates statistics, and provides insights.
    
    Args:
        data: Extracted data dictionary
        doc_type: Type of document being analyzed
        
    Returns:
        Analytics results with totals, averages, anomalies, and recommendations
    """
    import statistics
    import json
    
    sample_data = data.get("sample", [])
    all_rows = data.get("row_count", len(sample_data))
    
    if not sample_data:
        return {"error": "No data to analyze"}
    
    # Basic numeric analysis
    numeric_analysis = []
    anomalies = []
    
    for col in data.get("columns", []):
        try:
            values = [float(str(row.get(col, 0)).replace(',', '').replace('$', '')) 
                     for row in sample_data if row.get(col)]
            if values and len(values) > 1:
                mean_val = statistics.mean(values)
                stdev_val = statistics.stdev(values) if len(values) > 1 else 0
                
                numeric_analysis.append({
                    "column": col,
                    "total": sum(values),
                    "average": mean_val,
                    "min": min(values),
                    "max": max(values),
                    "std_dev": stdev_val
                })
                
                # Detect anomalies (values > 3 standard deviations from mean)
                if stdev_val > 0:
                    for idx, val in enumerate(values):
                        z_score = abs((val - mean_val) / stdev_val)
                        if z_score > 3:
                            anomalies.append({
                                "type": "outlier",
                                "column": col,
                                "row_index": idx,
                                "value": val,
                                "z_score": round(z_score, 2),
                                "severity": "high" if z_score > 4 else "medium",
                                "description": f"Value {val} in column '{col}' is {z_score:.1f} standard deviations from mean",
                                "recommendation": f"Review transaction in row {idx+1} - unusually {'high' if val > mean_val else 'low'} value"
                            })
        except (ValueError, TypeError):
            continue
    
    # Check for missing values
    for col in data.get("columns", []):
        missing_count = sum(1 for row in sample_data if not row.get(col) or str(row.get(col)).strip() == '')
        if missing_count > 0:
            anomalies.append({
                "type": "missing_data",
                "column": col,
                "count": missing_count,
                "severity": "medium" if missing_count < len(sample_data) * 0.1 else "high",
                "description": f"Column '{col}' has {missing_count} missing values",
                "recommendation": f"Fill in missing values in column '{col}' or verify data completeness"
            })
    
    # Check for duplicate rows
    seen_rows = set()
    duplicate_count = 0
    for row in sample_data:
        row_str = json.dumps(row, sort_keys=True)
        if row_str in seen_rows:
            duplicate_count += 1
        seen_rows.add(row_str)
    
    if duplicate_count > 0:
        anomalies.append({
            "type": "duplicate_rows",
            "count": duplicate_count,
            "severity": "medium",
            "description": f"Found {duplicate_count} duplicate rows in the data",
            "recommendation": "Review and remove duplicate entries to ensure data accuracy"
        })
    
    # Use Azure OpenAI for deeper analysis if configured
    ai_insights = None
    if os.getenv("AZURE_OPENAI_API_KEY"):
        try:
            from services.azure_llm_service import azure_llm
            data_str = json.dumps(sample_data[:10], indent=2)
            ai_analysis = azure_llm.analyze_financial_data(data_str, doc_type or "financial document")
            ai_insights = ai_analysis.get("analysis", "")
        except Exception as e:
            print(f"Azure OpenAI analysis failed: {e}")
    
    return {
        "total_rows": all_rows,
        "numeric_analysis": numeric_analysis,
        "anomalies_detected": len(anomalies),
        "anomalies": anomalies,
        "data_quality_score": max(0, 100 - (len(anomalies) * 10)),
        "ai_insights": ai_insights
    }


# Tool: Search Documents with RAG
def search_documents(query: str, user_id: str, top_k: int = 5) -> Dict[str, Any]:
    """
    Search uploaded financial documents using semantic similarity (RAG).
    
    This tool uses embeddings to find the most relevant data chunks that match
    the user's query. Perfect for answering questions about uploaded documents.
    
    Args:
        query: Natural language search query (e.g., "total invoice amount")
        user_id: User identifier for data isolation (required)
        top_k: Maximum number of results to return (default: 5)
        
    Returns:
        Dictionary containing:
        - query: Original search query
        - results: List of matching chunks with similarity scores
        - results_count: Number of results found
        - user_id: User identifier
        - status: "success" or error information
        
    Example:
        search_documents("What is the total amount?", "user123", 3)
        -> {"results": [{chunk_text: "...", score: 0.89}, ...], "results_count": 3}
    """
    from services import storage_service, embedding_service
    
    try:
        # Get embeddings for user's documents only
        bq_query = f"""
        SELECT e.embedding_id, e.document_id, e.row_index, e.chunk_text, e.embedding, e.metadata
        FROM `{os.getenv('GOOGLE_CLOUD_PROJECT')}.{os.getenv('BIGQUERY_DATASET', 'financial_close')}.embeddings` e
        JOIN `{os.getenv('GOOGLE_CLOUD_PROJECT')}.{os.getenv('BIGQUERY_DATASET', 'financial_close')}.documents` d
        ON e.document_id = d.document_id
        WHERE d.user_id = '{user_id}'
        LIMIT 1000
        """
        
        results = storage_service.bq_client.query(bq_query).result()
        embeddings_data = [dict(row) for row in results]
        
        if not embeddings_data:
            return {
                "query": query,
                "results": [],
                "message": "No documents found. Please upload documents first.",
                "user_id": user_id
            }
        
        # Search for similar chunks
        similar_chunks = embedding_service.search_similar(query, embeddings_data, top_k)
        
        # Add score field for compatibility
        for chunk in similar_chunks:
            chunk['score'] = chunk.get('similarity', 0)
        
        return {
            "query": query,
            "results_count": len(similar_chunks),
            "results": similar_chunks[:top_k],
            "user_id": user_id,
            "status": "success"
        }
    
    except Exception as e:
        return {
            "query": query,
            "error": str(e),
            "results": [],
            "user_id": user_id
        }


# Tool: Generate Report
def generate_month_end_report(user_id: str) -> Dict[str, Any]:
    """
    Generate comprehensive month-end close analysis report.
    
    This tool creates a detailed report including document summary, checklist status,
    financial analytics, anomaly detection, and actionable recommendations.
    
    Args:
        user_id: User identifier (required)
        
    Returns:
        Dictionary containing:
        - report: Full structured report with all sections
        - text_report: Human-readable formatted text version
        - total_documents: Count of uploaded documents
        - total_rows: Total data rows processed
        - completion_percentage: Checklist completion (e.g., "75%")
        - status: Overall status (COMPLETE, INCOMPLETE, etc.)
        - financial_summary: Totals, averages, transaction counts
        - anomalies: List of detected issues with severity and recommendations
        
    Example:
        generate_month_end_report("user123")
        -> {"total_documents": 8, "completion_percentage": "100%", "anomalies": [...]}
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
        
        # Perform deep analytics on all documents
        all_anomalies = []
        total_rows = 0
        financial_summary = {
            "total_amount": 0,
            "transaction_count": 0,
            "avg_amount": 0
        }
        
        for doc in documents:
            doc_id = doc.get("document_id")
            doc_type = doc.get("doc_type")
            
            # Get structured data for this document
            data_query = f"""
            SELECT data FROM `{os.getenv('GOOGLE_CLOUD_PROJECT')}.{os.getenv('BIGQUERY_DATASET', 'financial_close')}.structured_data`
            WHERE document_id = '{doc_id}'
            LIMIT 100
            """
            
            data_results = storage_service.bq_client.query(data_query).result()
            rows = [dict(row)['data'] for row in data_results]
            
            if rows:
                # Analyze this document
                analysis = analyze_financial_data({
                    "sample": rows,
                    "row_count": doc.get("row_count", len(rows)),
                    "columns": list(rows[0].keys()) if rows else []
                }, doc_type)
                
                # Collect anomalies
                if analysis.get("anomalies"):
                    for anomaly in analysis["anomalies"]:
                        anomaly["document_id"] = doc_id
                        anomaly["filename"] = doc.get("filename")
                        all_anomalies.append(anomaly)
                
                # Calculate financial totals
                for row in rows:
                    for key, value in row.items():
                        if any(term in key.lower() for term in ['amount', 'total', 'balance', 'value']):
                            try:
                                amount = float(str(value).replace(',', '').replace('$', ''))
                                financial_summary["total_amount"] += amount
                                financial_summary["transaction_count"] += 1
                            except (ValueError, TypeError):
                                pass
            
            total_rows += doc.get("row_count", 0)
        
        # Calculate averages
        if financial_summary["transaction_count"] > 0:
            financial_summary["avg_amount"] = financial_summary["total_amount"] / financial_summary["transaction_count"]
        
        # Get analytics summary
        analytics = {
            "total_documents": len(documents),
            "total_rows": total_rows,
            "anomalies_detected": len(all_anomalies),
            "anomalies": all_anomalies,
            "financial_summary": financial_summary
        }
        
        # Generate report
        report = report_service.generate_summary_report(
            user_id, documents, checklist, analytics
        )
        
        # Generate enhanced text version
        text_report = report_service.generate_detailed_text_report(report)
        
        return {
            "report": report,
            "text_report": text_report,
            "total_documents": len(documents),
            "total_rows": total_rows,
            "completion_percentage": f"{report['summary']['checklist_completion']['percentage']}%",
            "status": report['summary']['status'],
            "documents_by_type": report['summary']['documents_by_type'],
            "checklist_status": checklist,
            "financial_summary": financial_summary,
            "status": "success"
        }
    
    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc(),
            "status": "failed"
        }


# Main Orchestrator Agent
orchestrator_agent = Agent(
    model=LiteLlm(model=model_name),
    name="orchestrator_agent",
    description="""Expert financial document processor that automates month-end close workflows. 
    Classifies documents, extracts data, tracks completion, detects anomalies, and generates comprehensive reports.""",
    instruction="""You are an expert financial automation agent specializing in month-end close processes.

CORE CAPABILITIES:
- Document classification (bank statements, invoices, ledgers, reconciliations)
- CSV data extraction with intelligent parsing
- Checklist tracking and completion monitoring
- Financial analytics with anomaly detection
- Comprehensive report generation

WORKFLOW FOR DOCUMENT PROCESSING:
1. Classify the document using classify_document(filename, sample_data)
2. Extract and store data using extract_csv_data(content, doc_type, document_id)
3. Update checklist using check_checklist_status(user_id, doc_type)
4. Analyze data using analyze_financial_data(data, doc_type)
5. Summarize findings clearly and professionally

TOOL USAGE GUIDELINES:
- Always classify documents before extraction
- Use document_id consistently across operations
- Update checklist after successful extraction
- Run analytics to detect outliers, missing data, and duplicates
- Generate reports only when user requests or after batch uploads

COMMUNICATION STYLE:
- Professional and precise with financial terminology
- Clear explanations of detected issues
- Actionable recommendations for anomalies
- Concise summaries of processing results

IMPORTANT:
- Verify data quality before confirming success
- Flag high-severity anomalies immediately
- Maintain data accuracy and compliance standards
- Provide specific row/column references for issues""",
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
    model=LiteLlm(model=model_name),
    name="chatbot_agent",
    description="""Intelligent financial Q&A assistant with RAG-powered semantic search. 
    Answers questions about uploaded documents, explains data, and provides month-end close guidance.""",
    instruction="""You are an intelligent financial assistant specializing in month-end close support.

CORE CAPABILITIES:
- Answer questions using RAG (Retrieval-Augmented Generation)
- Search through uploaded financial documents semantically
- Explain checklist status and requirements
- Clarify anomalies and data quality issues
- Provide month-end close best practices

WORKFLOW FOR ANSWERING QUESTIONS:
1. Understand the user's question clearly
2. Use search_documents(query, user_id, top_k) to find relevant data
3. Analyze the retrieved context carefully
4. Formulate accurate answers based on actual data
5. Cite specific sources (document names, row numbers)

TOOL USAGE GUIDELINES:
- search_documents: Use for any data-related questions
- check_checklist_status: Use when asked about upload status or missing documents
- generate_month_end_report: Use when user requests a comprehensive report

COMMUNICATION STYLE:
- Conversational yet professional
- Reference specific data points from search results
- Use numbers and financial terms accurately
- Provide context and explanations
- Admit when information is not available

RESPONSE PATTERNS:
✓ "Based on your bank statement (uploaded Jan 15), the total is $X..."
✓ "I found 3 transactions matching your query in invoice_register.csv..."
✓ "Your checklist shows 3/4 documents uploaded. Missing: ledger"
✗ Avoid: "I think..." or "Maybe..." - be definitive or say you don't know

IMPORTANT:
- Always search before answering data questions
- Never make up numbers or facts
- If search returns no results, explain why and suggest alternatives
- Keep responses concise but informative""",
    tools=[
        check_checklist_status,
        search_documents,
        generate_month_end_report
    ]
)

# Set root agent
root_agent = orchestrator_agent
