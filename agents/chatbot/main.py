from fastapi import FastAPI
from pydantic import BaseModel
import os

app = FastAPI(title="Chatbot Agent")

class ChatRequest(BaseModel):
    message: str
    session_id: str
    user_id: str

# Simple in-memory chat history for demo
chat_history = {}

@app.post("/chat")
async def chat(request: ChatRequest):
    """Handle chat queries - simplified for demo"""
    
    session_id = request.session_id
    if session_id not in chat_history:
        chat_history[session_id] = []
    
    # Store user message
    chat_history[session_id].append({
        "role": "user",
        "content": request.message
    })
    
    # Simple rule-based responses for demo
    message_lower = request.message.lower()
    
    if "missing" in message_lower or "incomplete" in message_lower:
        response = "Based on the checklist, you're missing the Invoice Register and Bank Reconciliation documents. Please upload these to complete the month-end close."
    elif "status" in message_lower:
        response = "Your month-end close is 60% complete. You've uploaded Bank Statement and General Ledger. Still need Invoice Register and Bank Reconciliation."
    elif "anomal" in message_lower or "issue" in message_lower:
        response = "I detected 2 anomalies in your bank statement: Transaction #45 (amount $15,000) and #67 (amount $-8,500) are outliers. Would you like details?"
    elif "help" in message_lower:
        response = "I can help you with: checking document status, identifying missing items, explaining anomalies, and answering questions about your financial data."
    else:
        response = f"I understand you're asking about: '{request.message}'. For this demo, I can help with status checks, missing documents, and anomaly detection. Try asking 'What's my status?' or 'Show missing documents'."
    
    # Store bot response
    chat_history[session_id].append({
        "role": "assistant",
        "content": response
    })
    
    return {
        "response": response,
        "session_id": session_id,
        "history_length": len(chat_history[session_id])
    }

@app.get("/history/{session_id}")
async def get_history(session_id: str):
    """Get chat history for a session"""
    return {
        "session_id": session_id,
        "history": chat_history.get(session_id, [])
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}
