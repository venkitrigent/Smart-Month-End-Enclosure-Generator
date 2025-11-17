from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Checklist Agent")

REQUIRED_DOCS = {
    "bank_statement": {"name": "Bank Statement", "required": True},
    "invoice": {"name": "Invoice Register", "required": True},
    "ledger": {"name": "General Ledger", "required": True},
    "reconciliation": {"name": "Bank Reconciliation", "required": True},
    "schedule": {"name": "Depreciation Schedule", "required": False}
}

# In-memory storage for demo
checklist_status = {}

class ChecklistUpdate(BaseModel):
    doc_type: str
    user_id: str

@app.post("/update")
async def update_checklist(update: ChecklistUpdate):
    """Update checklist when document is uploaded"""
    
    user_id = update.user_id
    if user_id not in checklist_status:
        checklist_status[user_id] = {doc: "missing" for doc in REQUIRED_DOCS.keys()}
    
    checklist_status[user_id][update.doc_type] = "uploaded"
    
    # Calculate completion
    total = len([d for d in REQUIRED_DOCS.values() if d["required"]])
    completed = len([s for doc, s in checklist_status[user_id].items() 
                     if s == "uploaded" and REQUIRED_DOCS.get(doc, {}).get("required")])
    
    return {
        "user_id": user_id,
        "checklist": checklist_status[user_id],
        "completion_rate": f"{completed}/{total}",
        "percentage": round((completed / total) * 100, 1)
    }

@app.get("/status/{user_id}")
async def get_status(user_id: str):
    """Get current checklist status"""
    
    if user_id not in checklist_status:
        checklist_status[user_id] = {doc: "missing" for doc in REQUIRED_DOCS.keys()}
    
    return {
        "user_id": user_id,
        "checklist": checklist_status[user_id],
        "required_docs": REQUIRED_DOCS
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}
