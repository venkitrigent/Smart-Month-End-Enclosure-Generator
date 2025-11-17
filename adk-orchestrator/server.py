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
        
        return {
            "status": "success",
            "document_id": document_id,
            "classification": classification,
            "extraction": extraction,
            "checklist": checklist
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
    """Get checklist status for current user"""
    from month_end_agent.agent import check_checklist_status
    return check_checklist_status(current_user["user_id"])

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
    
    # Use chatbot agent to respond
    # In production, this would call the ADK agent properly
    # For now, return a structured response
    from month_end_agent.agent import search_documents
    
    # Search for relevant data
    search_results = search_documents(message, user_id, top_k=3)
    
    # Generate response (simplified)
    if search_results.get("results"):
        context = "\n".join([r.get("chunk_text", "") for r in search_results["results"][:2]])
        response = f"Based on your uploaded data:\n\n{context}\n\nHow can I help you further?"
    else:
        response = "I don't have enough data to answer that. Please upload documents first."
    
    # Save assistant response
    storage_service.save_chat_message(session_id, "assistant", response)
    
    return {
        "session_id": session_id,
        "message": message,
        "response": response,
        "search_results": search_results.get("results", []),
        "history_length": len(history) + 2
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
