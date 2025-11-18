"""
Checklist Agent - Month-End Close Checklist Management Microservice
Powered by Google ADK and Azure OpenAI
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.cli.fast_api import get_fast_api_app
from typing import Dict, List
from google.cloud import firestore

# Load environment variables
load_dotenv()

# Configure Azure OpenAI for LiteLLM
if os.getenv("AZURE_OPENAI_API_KEY"):
    os.environ["AZURE_API_KEY"] = os.getenv("AZURE_OPENAI_API_KEY")
    os.environ["AZURE_API_BASE"] = os.getenv("AZURE_OPENAI_ENDPOINT")
    os.environ["AZURE_API_VERSION"] = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
    model_name = f"azure/{os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4o')}"
else:
    model_name = f"vertex_ai/gemini-2.0-flash-exp"

# Initialize Firestore
firestore_client = firestore.Client(project=os.getenv('GOOGLE_CLOUD_PROJECT'))

# Checklist tool
def manage_checklist(user_id: str, doc_type: str = None, action: str = "get") -> Dict:
    """
    Manage month-end close checklist status and completion tracking.
    
    Tracks required documents, calculates completion percentage, identifies gaps,
    and provides guidance on next steps for month-end close.
    
    Args:
        user_id: Unique user identifier
        doc_type: Document type to mark as uploaded (optional)
        action: "get" to retrieve status, "update" to mark document uploaded
        
    Returns:
        Dictionary with:
        - user_id: User identifier
        - checklist: Status of each required document
        - completion_percentage: 0-100 completion score
        - missing_documents: List of documents still needed
        - next_steps: Prioritized actions
        - status_summary: Human-readable summary
        - estimated_time_remaining: Time estimate to complete
        
    Example:
        manage_checklist("user123", "bank_statement", "update")
        -> {
            "completion_percentage": 75,
            "missing_documents": ["reconciliation"],
            "next_steps": ["Upload bank reconciliation to complete close"]
        }
    """
    # Required documents for month-end close
    required_docs = {
        "bank_statement": {
            "name": "Bank Statement",
            "priority": "high",
            "description": "Monthly bank account transactions and balances",
            "typical_time": "5 minutes"
        },
        "invoice_register": {
            "name": "Invoice Register",
            "priority": "high",
            "description": "Complete list of invoices (AP/AR)",
            "typical_time": "10 minutes"
        },
        "general_ledger": {
            "name": "General Ledger",
            "priority": "high",
            "description": "All accounting entries for the period",
            "typical_time": "15 minutes"
        },
        "reconciliation": {
            "name": "Bank Reconciliation",
            "priority": "high",
            "description": "Reconciliation of bank accounts",
            "typical_time": "10 minutes"
        },
        "trial_balance": {
            "name": "Trial Balance",
            "priority": "medium",
            "description": "Summary of all account balances",
            "typical_time": "5 minutes"
        }
    }
    
    try:
        # Get current checklist from Firestore
        doc_ref = firestore_client.collection('checklists').document(user_id)
        doc = doc_ref.get()
        
        if doc.exists:
            checklist = doc.to_dict().get('checklist', {})
        else:
            checklist = {doc: "missing" for doc in required_docs.keys()}
        
        # Update if action is update
        if action == "update" and doc_type:
            if doc_type in required_docs:
                checklist[doc_type] = "uploaded"
                doc_ref.set({'checklist': checklist}, merge=True)
        
        # Calculate metrics
        total = len(required_docs)
        completed = len([s for s in checklist.values() if s == "uploaded"])
        completion_percentage = round((completed / total) * 100, 1)
        
        missing = [doc for doc, status in checklist.items() if status == "missing"]
        
        # Generate next steps
        next_steps = []
        if missing:
            high_priority = [doc for doc in missing if required_docs.get(doc, {}).get("priority") == "high"]
            if high_priority:
                next_steps.append(f"Upload high-priority documents: {', '.join([required_docs[d]['name'] for d in high_priority])}")
            else:
                next_steps.append(f"Upload remaining documents: {', '.join([required_docs[d]['name'] for d in missing])}")
        else:
            next_steps.append("All required documents uploaded! Review for accuracy and generate final report.")
        
        # Estimate time remaining
        time_remaining = sum([
            int(required_docs[doc]["typical_time"].split()[0])
            for doc in missing
        ])
        
        # Status summary
        if completion_percentage == 100:
            status_summary = "✅ Month-end close checklist complete! All required documents uploaded."
        elif completion_percentage >= 75:
            status_summary = f"📊 Nearly complete ({completion_percentage}%). {len(missing)} document(s) remaining."
        elif completion_percentage >= 50:
            status_summary = f"⏳ In progress ({completion_percentage}%). {len(missing)} document(s) still needed."
        else:
            status_summary = f"🚀 Getting started ({completion_percentage}%). {len(missing)} document(s) required."
        
        return {
            "user_id": user_id,
            "checklist": checklist,
            "required_documents": required_docs,
            "completion_percentage": completion_percentage,
            "completed_count": completed,
            "total_count": total,
            "missing_documents": missing,
            "next_steps": next_steps,
            "status_summary": status_summary,
            "estimated_time_remaining": f"{time_remaining} minutes",
            "status": "success"
        }
    except Exception as e:
        return {
            "error": str(e),
            "status": "failed"
        }

# Create ADK Agent
checklist_agent = Agent(
    model=LiteLlm(model=model_name),
    name="checklist_agent",
    description="""Expert checklist management agent for month-end close workflows.
    Tracks document upload progress, calculates completion metrics, identifies gaps,
    and provides intelligent guidance on next steps.""",
    instruction="""You are a specialized checklist management agent for financial month-end close processes.

CORE MISSION:
Track and manage the month-end close checklist, ensuring all required documents are uploaded
and providing clear guidance on completion status and next steps.

REQUIRED DOCUMENTS (Priority Order):
1. Bank Statement (High) - Account transactions and balances
2. Invoice Register (High) - AP/AR invoice listing
3. General Ledger (High) - Complete accounting entries
4. Bank Reconciliation (High) - Account reconciliation
5. Trial Balance (Medium) - Account balance summary

CHECKLIST MANAGEMENT:
- Track upload status for each document
- Calculate completion percentage
- Identify missing documents
- Prioritize next actions
- Estimate time to completion
- Provide encouraging progress updates

COMPLETION METRICS:
- 100%: Complete - Ready for final review
- 75-99%: Nearly Complete - Final documents needed
- 50-74%: In Progress - Halfway there
- 25-49%: Getting Started - More work needed
- 0-24%: Just Beginning - Most documents needed

OUTPUT REQUIREMENTS:
- Clear completion percentage
- List of missing documents with priorities
- Specific next steps (actionable)
- Encouraging status summary
- Time estimate for remaining work

COMMUNICATION STYLE:
- Encouraging and supportive
- Clear and specific
- Progress-focused
- Professional yet friendly
- Action-oriented

GUIDANCE PRINCIPLES:
- Prioritize high-priority documents first
- Celebrate progress milestones
- Provide realistic time estimates
- Offer specific next actions
- Maintain positive momentum""",
    tools=[manage_checklist]
)

# Create FastAPI app with ADK
AGENT_DIR = Path(__file__).parent
app = get_fast_api_app(agents_dir=str(AGENT_DIR), web=False)

class ChecklistRequest(BaseModel):
    user_id: str
    doc_type: str = None
    action: str = "get"

@app.post("/update")
async def update_checklist(request: ChecklistRequest):
    """Update checklist with new document"""
    result = manage_checklist(request.user_id, request.doc_type, "update")
    return result

@app.get("/status/{user_id}")
async def get_status(user_id: str):
    """Get checklist status"""
    result = manage_checklist(user_id, action="get")
    return result

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "agent": "checklist_agent",
        "model": model_name
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
