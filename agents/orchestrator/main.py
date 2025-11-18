"""
Orchestrator Agent - Master Workflow Coordination Microservice
Simple FastAPI orchestrator that routes requests to specialized agents
"""
import os
from fastapi import FastAPI, UploadFile, File, Form
from pydantic import BaseModel
from typing import Dict, List
import httpx
import uuid

# Agent service URLs from environment
CLASSIFIER_URL = os.getenv('CLASSIFIER_URL', 'http://localhost:8001')
EXTRACTOR_URL = os.getenv('EXTRACTOR_URL', 'http://localhost:8002')
CHECKLIST_URL = os.getenv('CHECKLIST_URL', 'http://localhost:8003')
ANALYTICS_URL = os.getenv('ANALYTICS_URL', 'http://localhost:8004')
CHATBOT_URL = os.getenv('CHATBOT_URL', 'http://localhost:8005')
REPORT_URL = os.getenv('REPORT_URL', 'http://localhost:8006')

# Create FastAPI app
app = FastAPI(
    title="Orchestrator Agent",
    description="Master coordinator for month-end close multi-agent system",
    version="1.0.0"
)

# Orchestration tool
async def orchestrate_document_processing(
    filename: str,
    file_content: bytes,
    user_id: str,
    document_id: str = None
) -> Dict:
    """
    Orchestrate complete document processing workflow across all agents.
    
    Coordinates classification, extraction, checklist updates, and analytics
    in a sequential workflow with error handling and status tracking.
    
    Args:
        filename: Name of uploaded file
        file_content: Raw file bytes
        user_id: User identifier
        document_id: Optional document ID
        
    Returns:
        Dictionary with results from all processing stages
    """
    if not document_id:
        document_id = str(uuid.uuid4())
    
    results = {
        "document_id": document_id,
        "filename": filename,
        "user_id": user_id,
        "workflow_status": "in_progress"
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Step 1: Classify Document
            classify_response = await client.post(
                f"{CLASSIFIER_URL}/classify",
                files={"file": (filename, file_content)}
            )
            classification = classify_response.json()
            results["classification"] = classification
            doc_type = classification.get("doc_type", "unknown")
            
            # Step 2: Extract Data
            extract_response = await client.post(
                f"{EXTRACTOR_URL}/extract",
                files={"file": (filename, file_content)},
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

# Create ADK Agent
orchestrator_agent = Agent(
    model=LiteLlm(model=model_name),
    name="orchestrator_agent",
    description="""Master orchestration agent coordinating all month-end close workflows.
    Manages document processing pipeline, coordinates specialized agents, handles errors,
    and ensures smooth end-to-end workflow execution.""",
    instruction="""You are the master orchestrator agent for the Smart Month-End Close system.

CORE MISSION:
Coordinate and manage the complete month-end close workflow by orchestrating
specialized agents for classification, extraction, checklist management, analytics,
chat, and report generation.

WORKFLOW ORCHESTRATION:
1. Document Upload → Classifier Agent
2. Classification → Extractor Agent
3. Extraction → Checklist Agent (update status)
4. Extraction → Analytics Agent (analyze data)
5. User Request → Chatbot Agent (Q&A)
6. Final Step → Report Composer Agent (generate report)

AGENT COORDINATION:
- Classifier Agent: Document type identification
- Extractor Agent: CSV parsing and validation
- Checklist Agent: Progress tracking
- Analytics Agent: Data analysis and anomaly detection
- Chatbot Agent: User Q&A with RAG
- Report Composer Agent: Final report generation

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

# FastAPI app already created above

@app.post("/process-upload")
async def process_upload(
    file: UploadFile = File(...),
    user_id: str = Form("demo_user")
):
    """Orchestrate complete document processing workflow"""
    content = await file.read()
    result = await orchestrate_document_processing(
        file.filename,
        content,
        user_id
    )
    return result

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
    uvicorn.run(app, host="0.0.0.0", port=8000)
