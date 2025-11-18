"""
Orchestrator Agent - Master Workflow Coordination Microservice
ADK Agent that orchestrates calls to specialized agents via HTTP
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, Form
from pydantic import BaseModel
from typing import Dict, List
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.cli.fast_api import get_fast_api_app
import httpx
import uuid

# Load environment variables
load_dotenv()

# Configure model
if os.getenv("AZURE_OPENAI_API_KEY"):
    model_name = f"vertex_ai/gemini-2.0-flash-exp"
else:
    model_name = f"vertex_ai/{os.getenv('GEMINI_MODEL', 'gemini-2.0-flash-exp')}"

# Agent service URLs from environment
CLASSIFIER_URL = os.getenv('CLASSIFIER_URL', 'http://localhost:8001')
EXTRACTOR_URL = os.getenv('EXTRACTOR_URL', 'http://localhost:8002')
CHECKLIST_URL = os.getenv('CHECKLIST_URL', 'http://localhost:8003')
ANALYTICS_URL = os.getenv('ANALYTICS_URL', 'http://localhost:8004')
CHATBOT_URL = os.getenv('CHATBOT_URL', 'http://localhost:8005')
REPORT_URL = os.getenv('REPORT_URL', 'http://localhost:8006')

# Orchestration tool - calls other agents via HTTP
def orchestrate_document_processing(
    filename: str,
    file_content: str,
    user_id: str,
    document_id: str = None
) -> Dict:
    """
    Orchestrate complete document processing workflow across all agents.
    
    Coordinates classification, extraction, checklist updates, and analytics
    in a sequential workflow with error handling and status tracking.
    
    This tool makes HTTP calls to other deployed agents to coordinate the workflow.
    
    Args:
        filename: Name of uploaded file
        file_content: File content as string (will be converted to bytes for HTTP)
        user_id: User identifier
        document_id: Optional document ID
        
    Returns:
        Dictionary with results from all processing stages
    """
    import asyncio
    
    if not document_id:
        document_id = str(uuid.uuid4())
    
    results = {
        "document_id": document_id,
        "filename": filename,
        "user_id": user_id,
        "workflow_status": "in_progress"
    }
    
    async def _orchestrate():
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Convert string content to bytes if needed
                file_bytes = file_content.encode('utf-8') if isinstance(file_content, str) else file_content
                
                # Step 1: Classify Document
                classify_response = await client.post(
                    f"{CLASSIFIER_URL}/classify",
                    files={"file": (filename, file_bytes)}
                )
                classification = classify_response.json()
                results["classification"] = classification
                doc_type = classification.get("doc_type", "unknown")
                
                # Step 2: Extract Data
                extract_response = await client.post(
                    f"{EXTRACTOR_URL}/extract",
                    files={"file": (filename, file_bytes)},
                    data={"doc_type": doc_type, "document_id": document_id}
                )
                extraction = extract_response.json()
                results["extraction"] = extraction
                
                # Step 3: Update Checklist
                checklist_response = await client.post(
                    f"{CHECKLIST_URL}/update",
                    json={"user_id": user_id, "doc_type": doc_type, "action": "update"}
                )
                checklist = checklist_response.json()
                results["checklist"] = checklist
                
                # Step 4: Run Analytics
                analytics_response = await client.post(
                    f"{ANALYTICS_URL}/analyze",
                    json={"data": extraction, "doc_type": doc_type}
                )
                analytics = analytics_response.json()
                results["analytics"] = analytics
                
                results["workflow_status"] = "completed"
                results["status"] = "success"
                
                return results
                
        except Exception as e:
            results["workflow_status"] = "failed"
            results["error"] = str(e)
            results["status"] = "error"
            return results
    
    # Run async function synchronously for ADK tool
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(_orchestrate())

# Create ADK Agent
orchestrator_agent = Agent(
    model=LiteLlm(model=model_name),
    name="orchestrator_agent",
    description="""Master orchestration agent coordinating all month-end close workflows.
    Manages document processing pipeline, coordinates specialized agents via HTTP calls, handles errors,
    and ensures smooth end-to-end workflow execution.""",
    instruction="""You are the master orchestrator agent for the Smart Month-End Close system.

CORE MISSION:
Coordinate and manage the complete month-end close workflow by orchestrating
specialized agents for classification, extraction, checklist management, analytics,
chat, and report generation.

WORKFLOW ORCHESTRATION:
1. Document Upload → Classifier Agent (HTTP call)
2. Classification → Extractor Agent (HTTP call)
3. Extraction → Checklist Agent (HTTP call) - update status
4. Extraction → Analytics Agent (HTTP call) - analyze data
5. User Request → Chatbot Agent (HTTP call) - Q&A
6. Final Step → Report Composer Agent (HTTP call) - generate report

AGENT COORDINATION:
- Classifier Agent: Document type identification via HTTP
- Extractor Agent: CSV parsing and validation via HTTP
- Checklist Agent: Progress tracking via HTTP
- Analytics Agent: Data analysis and anomaly detection via HTTP
- Chatbot Agent: User Q&A with RAG via HTTP
- Report Composer Agent: Final report generation via HTTP

ERROR HANDLING:
- Graceful degradation if agents fail
- Clear error messages to users
- Retry logic for transient failures
- Status tracking throughout workflow
- Rollback capabilities when needed

WORKFLOW STATES:
- pending: Workflow initiated
- in_progress: Processing underway
- completed: Successfully finished
- failed: Error occurred
- partial: Some steps completed

COMMUNICATION STYLE:
- Clear status updates
- Specific error messages
- Progress indicators
- Professional tone
- Actionable guidance

QUALITY STANDARDS:
- Ensure all agents complete successfully
- Validate data between steps
- Track workflow state
- Provide detailed results
- Handle errors gracefully""",
    tools=[orchestrate_document_processing]
)

# Create FastAPI app
# Note: We use a simple FastAPI app instead of get_fast_api_app() 
# because the orchestrator mainly routes to other agents via HTTP
app = FastAPI(
    title="Orchestrator Agent",
    description="Master coordinator for month-end close multi-agent system",
    version="1.0.0"
)

@app.post("/upload")
async def upload_single(
    file: UploadFile = File(...),
    user_id: str = Form("demo_user")
):
    """Upload and process single document (frontend endpoint)"""
    content = await file.read()
    content_str = content.decode('utf-8') if isinstance(content, bytes) else content
    result = orchestrate_document_processing(
        file.filename,
        content_str,
        user_id
    )
    return result

@app.post("/process-upload")
async def process_upload(
    file: UploadFile = File(...),
    user_id: str = Form("demo_user")
):
    """Orchestrate complete document processing workflow (alias for /upload)"""
    return await upload_single(file, user_id)

@app.post("/upload-multiple")
async def upload_multiple(
    files: List[UploadFile] = File(...),
    user_id: str = Form(default="demo_user")
):
    """Upload and process multiple documents"""
    results = []
    errors = []
    files_processed = 0
    files_failed = 0
    
    for file in files:
        try:
            content = await file.read()
            content_str = content.decode('utf-8') if isinstance(content, bytes) else content
            result = orchestrate_document_processing(
                file.filename,
                content_str,
                user_id
            )
            
            if result.get("status") == "success":
                files_processed += 1
                results.append({
                    "filename": file.filename,
                    "doc_type": result.get("classification", {}).get("doc_type", "unknown"),
                    "rows_processed": result.get("extraction", {}).get("row_count", 0),
                    **result
                })
            else:
                files_failed += 1
                errors.append({
                    "filename": file.filename,
                    "error": result.get("error", "Unknown error")
                })
        except Exception as e:
            files_failed += 1
            errors.append({
                "filename": file.filename,
                "error": str(e)
            })
    
    # Generate report if all files processed successfully
    report = None
    if files_processed > 0 and files_failed == 0:
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                checklist_response = await client.get(f"{CHECKLIST_URL}/status/{user_id}")
                checklist = checklist_response.json()
                
                report_response = await client.post(
                    f"{REPORT_URL}/generate",
                    json={
                        "user_id": user_id,
                        "documents": results,
                        "checklist": checklist,
                        "analytics": {},
                        "report_type": "executive"
                    }
                )
                report = report_response.json()
        except Exception as e:
            pass  # Report generation is optional
    
    return {
        "files_processed": files_processed,
        "files_failed": files_failed,
        "results": results,
        "errors": errors,
        "report": report
    }

@app.post("/generate-report")
async def generate_report(user_id: str = Form(...)):
    """Generate comprehensive month-end close report"""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Get checklist status
            checklist_response = await client.get(f"{CHECKLIST_URL}/status/{user_id}")
            checklist = checklist_response.json()
            
            # For now, use mock data for documents and analytics
            # In production, this would query from storage
            documents = []
            analytics = {
                "anomalies": [],
                "risk_level": "MINIMAL",
                "risk_summary": "No significant issues detected",
                "recommendations": ["Review all documents before finalizing"]
            }
            
            # Generate report
            report_response = await client.post(
                f"{REPORT_URL}/generate",
                json={
                    "user_id": user_id,
                    "documents": documents,
                    "checklist": checklist,
                    "analytics": analytics,
                    "report_type": "executive"
                }
            )
            
            return report_response.json()
            
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

@app.post("/chat")
async def chat(
    message: str = Form(...),
    user_id: str = Form(...),
    session_id: str = Form(None)
):
    """Handle chat queries via chatbot agent"""
    if not session_id:
        session_id = str(uuid.uuid4())
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{CHATBOT_URL}/chat",
                json={
                    "message": message,
                    "user_id": user_id,
                    "session_id": session_id
                }
            )
            return response.json()
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "response": "I'm having trouble connecting. Please try again."
        }

@app.get("/checklist")
async def get_checklist(user_id: str = "demo_user"):
    """Get checklist status for user"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{CHECKLIST_URL}/status/{user_id}")
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "checklist": {},
                    "required_docs": {},
                    "completion_rate": "0/0",
                    "percentage": 0,
                    "missing": []
                }
    except Exception as e:
        return {
            "checklist": {},
            "required_docs": {},
            "completion_rate": "0/0",
            "percentage": 0,
            "missing": [],
            "error": str(e)
        }

@app.get("/me")
async def get_user_info():
    """Get current user information"""
    return {
        "user_id": "demo_user",
        "email": "demo@example.com",
        "authenticated": True
    }

@app.get("/health")
async def health():
    """Check health of orchestrator and all agents"""
    health_status = {
        "orchestrator": "healthy",
        "agents": {}
    }
    
    agent_urls = {
        "classifier": CLASSIFIER_URL,
        "extractor": EXTRACTOR_URL,
        "checklist": CHECKLIST_URL,
        "analytics": ANALYTICS_URL,
        "chatbot": CHATBOT_URL,
        "report": REPORT_URL
    }
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        for agent_name, url in agent_urls.items():
            try:
                response = await client.get(f"{url}/health")
                health_status["agents"][agent_name] = "healthy" if response.status_code == 200 else "unhealthy"
            except:
                health_status["agents"][agent_name] = "unreachable"
    
    return health_status

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
