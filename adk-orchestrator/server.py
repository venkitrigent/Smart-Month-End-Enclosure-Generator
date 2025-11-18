"""
FastAPI Server for Month-End Close ADK Agent
"""

import os
from dotenv import load_dotenv
from typing import List
from fastapi import FastAPI, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from google.adk.cli.fast_api import get_fast_api_app
from services import auth_service, storage_service
import uuid

# Load environment variables
load_dotenv()

AGENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Create FastAPI app with ADK integration
app_args = {
    "agents_dir": AGENT_DIR,
    "web": True  # Enable ADK web interface
}

app: FastAPI = get_fast_api_app(**app_args)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Update app metadata
app.title = "Smart Month-End Close - ADK Agent"
app.description = "AI-powered financial close automation with Vertex AI"
app.version = "1.0.0"

@app.get("/health")
def health_check():
    """Health check endpoint for Cloud Run"""
    return {
        "status": "healthy",
        "service": "month-end-close-agent",
        "version": "1.0.0",
        "features": {
            "bigquery": True,
            "firestore": True,
            "embeddings": True,
            "firebase_auth": auth_service.firebase_initialized,
            "api_key_auth": True
        }
    }


@app.get("/me")
async def get_current_user_info(
    current_user: dict = Depends(auth_service.get_current_user)
):
    """Get current authenticated user information"""
    return {
        "user_id": current_user["user_id"],
        "email": current_user.get("email", ""),
        "email_verified": current_user.get("email_verified", False),
        "auth_method": current_user.get("auth_method", "firebase")
    }

@app.get("/")
def root():
    """Root endpoint with service information"""
    return {
        "service": "Smart Month-End Close - ADK Agent",
        "description": "AI-powered financial close automation",
        "docs": "/docs",
        "web_ui": "/web",
        "health": "/health",
        "agents": ["orchestrator_agent", "chatbot_agent"],
        "features": ["BigQuery", "Firestore", "Embeddings", "RAG", "Authentication"]
    }

@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(auth_service.get_current_user)
):
    """
    Upload and process a single CSV document
    Requires Firebase Auth or API key
    """
    user_id = current_user["user_id"]
    
    try:
        # Read file content
        content = await file.read()
        content_str = content.decode('utf-8')
        
        # Generate document ID
        document_id = str(uuid.uuid4())
        
        # Process with agent tools
        from month_end_agent.agent import classify_document, extract_csv_data, check_checklist_status
        
        # Classify
        classification = classify_document(file.filename)
        doc_type = classification["doc_type"]
        
        # Extract and save
        extraction = extract_csv_data(content_str, doc_type, document_id)
        
        # Update checklist
        checklist = check_checklist_status(user_id, doc_type)
        
        # Save document metadata
        if "row_count" in extraction and "columns" in extraction:
            storage_service.save_document(
                document_id=document_id,
                filename=file.filename,
                doc_type=doc_type,
                user_id=user_id,
                row_count=extraction["row_count"],
                columns=extraction["columns"]
            )
        
        # Verify embeddings were created
        embeddings_verified = False
        if extraction.get("embeddings_generated", 0) > 0:
            embeddings_verified = storage_service.verify_embeddings(document_id)
        
        return {
            "status": "success",
            "document_id": document_id,
            "classification": classification,
            "extraction": extraction,
            "checklist": checklist,
            "embeddings_verified": embeddings_verified,
            "embeddings_count": extraction.get("embeddings_generated", 0)
        }
    
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@app.post("/upload-multiple")
async def upload_multiple_documents(
    files: List[UploadFile] = File(...),
    current_user: dict = Depends(auth_service.get_current_user)
):
    """
    Upload and process multiple CSV documents
    Complete workflow: Upload → Process → Generate Report
    Requires Firebase Auth or API key
    """
    user_id = current_user["user_id"]
    
    from month_end_agent.agent import (
        classify_document, 
        extract_csv_data, 
        check_checklist_status,
        generate_month_end_report
    )
    
    results = []
    errors = []
    
    # Process each file
    for file in files:
        try:
            # Read file content
            content = await file.read()
            content_str = content.decode('utf-8')
            
            # Generate document ID
            document_id = str(uuid.uuid4())
            
            # Classify
            classification = classify_document(file.filename)
            doc_type = classification["doc_type"]
            
            # Extract and save
            extraction = extract_csv_data(content_str, doc_type, document_id)
            
            # Update checklist
            checklist = check_checklist_status(user_id, doc_type)
            
            # Save document metadata
            if "row_count" in extraction and "columns" in extraction:
                storage_service.save_document(
                    document_id=document_id,
                    filename=file.filename,
                    doc_type=doc_type,
                    user_id=user_id,
                    row_count=extraction["row_count"],
                    columns=extraction["columns"]
                )
            
            results.append({
                "filename": file.filename,
                "document_id": document_id,
                "doc_type": doc_type,
                "status": "success",
                "rows_processed": extraction.get("row_count", 0)
            })
        
        except Exception as e:
            errors.append({
                "filename": file.filename,
                "error": str(e)
            })
    
    # Generate comprehensive report
    report = generate_month_end_report(user_id)
    
    return {
        "status": "success",
        "files_processed": len(results),
        "files_failed": len(errors),
        "results": results,
        "errors": errors,
        "report": report
    }

@app.get("/checklist")
async def get_checklist(
    current_user: dict = Depends(auth_service.get_current_user)
):
    """Get checklist status for current user with document counts"""
    from month_end_agent.agent import check_checklist_status
    user_id = current_user["user_id"]
    
    # Get checklist status
    checklist_data = check_checklist_status(user_id)
    
    # Get actual document counts from BigQuery
    try:
        doc_query = f"""
        SELECT doc_type, COUNT(*) as count
        FROM `{os.getenv('GOOGLE_CLOUD_PROJECT')}.{os.getenv('BIGQUERY_DATASET', 'financial_close')}.documents`
        WHERE user_id = '{user_id}'
        GROUP BY doc_type
        """
        results = storage_service.bq_client.query(doc_query).result()
        doc_counts = {row['doc_type']: row['count'] for row in results}
        
        # Update checklist with actual counts
        for doc_type in checklist_data.get('checklist', {}).keys():
            if doc_type in doc_counts or doc_type.replace('_', '') in doc_counts:
                checklist_data['checklist'][doc_type] = 'uploaded'
        
        checklist_data['document_counts'] = doc_counts
    except Exception as e:
        print(f"Error getting document counts: {e}")
    
    return checklist_data

@app.get("/data/{doc_type}")
async def get_data(
    doc_type: str,
    limit: int = 100,
    current_user: dict = Depends(auth_service.get_current_user)
):
    """Query structured data from BigQuery"""
    data = storage_service.query_data(doc_type, limit)
    return {
        "doc_type": doc_type,
        "count": len(data),
        "data": data
    }


@app.post("/search")
async def search_documents_endpoint(
    query: str,
    top_k: int = 5,
    current_user: dict = Depends(auth_service.get_current_user)
):
    """Search uploaded documents using RAG"""
    from month_end_agent.agent import search_documents
    return search_documents(query, current_user["user_id"], top_k)


@app.post("/generate-report")
async def generate_report_endpoint(
    current_user: dict = Depends(auth_service.get_current_user)
):
    """Generate month-end close report"""
    from month_end_agent.agent import generate_month_end_report
    return generate_month_end_report(current_user["user_id"])


@app.post("/chat")
async def chat_with_data(
    message: str,
    session_id: str = None,
    current_user: dict = Depends(auth_service.get_current_user)
):
    """
    Chat with uploaded data using RAG-powered chatbot
    Maintains conversation history in Firestore
    Requires Firebase Auth or API key
    """
    user_id = current_user["user_id"]
    
    if not session_id:
        session_id = str(uuid.uuid4())
    
    # Save user message
    storage_service.save_chat_message(session_id, "user", message)
    
    # Get chat history for context
    history = storage_service.get_chat_history(session_id)
    
    # Use RAG to search for relevant data
    from month_end_agent.agent import search_documents
    
    # Search for relevant data
    search_results = search_documents(message, user_id, top_k=5)
    
    # Generate response using Azure OpenAI if available
    response = ""
    if search_results.get("results") and len(search_results["results"]) > 0:
        # Build context from search results
        context_parts = []
        for idx, result in enumerate(search_results["results"][:3], 1):
            context_parts.append(f"[Source {idx}] {result.get('chunk_text', '')}")
        
        context = "\n\n".join(context_parts)
        
        # Try to use Azure OpenAI for intelligent response
        if os.getenv("AZURE_OPENAI_API_KEY"):
            try:
                from services.azure_llm_service import azure_llm
                
                # Build conversation history
                history_text = "\n".join([
                    f"{msg.get('role', 'user')}: {msg.get('content', '')}"
                    for msg in history[-5:]  # Last 5 messages
                ])
                
                ai_response = azure_llm.chat_with_context(
                    query=message,
                    context=context,
                    history=history_text
                )
                response = ai_response.get("response", "")
            except Exception as e:
                print(f"Azure OpenAI chat failed: {e}")
                response = f"Based on your uploaded data:\n\n{context}\n\nI found {len(search_results['results'])} relevant records. How can I help you analyze this further?"
        else:
            # Fallback response
            response = f"Based on your uploaded data, I found {len(search_results['results'])} relevant records:\n\n{context}\n\nHow can I help you analyze this further?"
    else:
        # No results found
        response = "I couldn't find relevant data to answer your question. This could mean:\n\n"
        response += "1. No documents have been uploaded yet\n"
        response += "2. The uploaded documents don't contain information related to your query\n"
        response += "3. Try rephrasing your question\n\n"
        response += "Please upload financial documents first, or try asking about:\n"
        response += "- Document upload status\n"
        response += "- Checklist completion\n"
        response += "- Available document types"
    
    # Save assistant response
    storage_service.save_chat_message(session_id, "assistant", response)
    
    return {
        "session_id": session_id,
        "message": message,
        "response": response,
        "search_results": search_results.get("results", []),
        "results_count": len(search_results.get("results", [])),
        "history_length": len(history) + 2,
        "user_id": user_id
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
