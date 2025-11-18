"""
Chatbot Agent - RAG-Powered Financial Q&A Microservice
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
import httpx

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

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

# Chatbot tool
def answer_financial_question(question: str, user_id: str, session_id: str) -> Dict:
    """
    Answer financial questions using RAG (Retrieval-Augmented Generation).
    
    Searches uploaded documents for relevant context, retrieves conversation history,
    and generates intelligent, context-aware responses using AI.
    
    Args:
        question: User's question about their financial data
        user_id: User identifier for data isolation
        session_id: Session identifier for conversation continuity
        
    Returns:
        Dictionary with:
        - response: AI-generated answer
        - sources: Relevant data chunks used
        - confidence: Response confidence level
        - suggestions: Follow-up questions or actions
        
    Example:
        answer_financial_question("What's my total?", "user123", "session456")
        -> {
            "response": "Based on your bank statement, the total is $45,230.50...",
            "sources": [{document: "bank_statement.csv", ...}],
            "confidence": "high"
        }
    """
    try:
        # Get conversation history from Firestore
        messages_ref = firestore_client.collection('sessions').document(session_id).collection('messages')
        history_docs = messages_ref.order_by('timestamp').limit(10).stream()
        history = [{"role": msg.to_dict().get('role'), "content": msg.to_dict().get('content')} 
                   for msg in history_docs]
        
        # Search for relevant context using BigQuery embeddings
        context = "No specific data context available. Please upload documents first."
        sources = []
        
        try:
            # Import embedding and storage services
            sys.path.append(str(Path(__file__).parent.parent.parent / 'adk-orchestrator'))
            from services.embedding_service import embedding_service
            from google.cloud import bigquery
            
            # Generate query embedding
            query_embedding = embedding_service.generate_embeddings([question])[0]
            
            # Search BigQuery for similar embeddings
            bq_client = bigquery.Client(project=os.getenv('GOOGLE_CLOUD_PROJECT'))
            
            search_query = f"""
            SELECT 
                e.embedding_id,
                e.document_id,
                e.row_index,
                e.chunk_text,
                e.embedding,
                d.filename,
                d.doc_type
            FROM `{os.getenv('GOOGLE_CLOUD_PROJECT')}.{os.getenv('BIGQUERY_DATASET', 'financial_close')}.embeddings` e
            JOIN `{os.getenv('GOOGLE_CLOUD_PROJECT')}.{os.getenv('BIGQUERY_DATASET', 'financial_close')}.documents` d
            ON e.document_id = d.document_id
            WHERE d.user_id = '{user_id}'
            LIMIT 100
            """
            
            results = bq_client.query(search_query).result()
            embeddings_data = [dict(row) for row in results]
            
            if embeddings_data:
                # Calculate cosine similarity
                similarities = []
                for item in embeddings_data:
                    embedding = item.get("embedding", [])
                    if not embedding:
                        continue
                    
                    # Cosine similarity
                    dot_product = sum(a * b for a, b in zip(query_embedding, embedding))
                    norm_a = sum(a * a for a in query_embedding) ** 0.5
                    norm_b = sum(b * b for b in embedding) ** 0.5
                    
                    if norm_a > 0 and norm_b > 0:
                        similarity = dot_product / (norm_a * norm_b)
                        similarities.append({
                            **item,
                            "similarity": similarity,
                            "score": similarity
                        })
                
                # Sort by similarity
                similarities.sort(key=lambda x: x["similarity"], reverse=True)
                sources = similarities[:3]
                
                if sources:
                    context = "\n\n".join([
                        f"[Source {i+1} - {s.get('filename', 'N/A')}] {s.get('chunk_text', '')}"
                        for i, s in enumerate(sources)
                    ])
        except Exception as e:
            print(f"Error searching embeddings: {e}")
            pass
        
        # Generate response using Azure OpenAI
        if os.getenv("AZURE_OPENAI_API_KEY"):
            from openai import AzureOpenAI
            client = AzureOpenAI(
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
            )
            
            # Build conversation
            messages = [
                {"role": "system", "content": """You are a helpful financial assistant for month-end close processes.
                
Answer questions based on the provided context from uploaded financial documents.
- Be specific and reference actual data
- If context is insufficient, say so clearly
- Provide actionable insights
- Keep responses concise but informative
- Use professional financial terminology"""},
                {"role": "user", "content": f"""Context from uploaded documents:
{context}

Previous conversation:
{chr(10).join([f"{h['role']}: {h['content']}" for h in history[-3:]])}

User question: {question}

Provide a helpful, accurate answer based on the context above."""}
            ]
            
            response = client.chat.completions.create(
                model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
                messages=messages,
                temperature=0.3,
                max_tokens=500
            )
            
            answer = response.choices[0].message.content
            confidence = "high" if sources else "low"
            
        else:
            # Fallback response
            if sources:
                answer = f"Based on your uploaded data:\n\n{context}\n\nI found {len(sources)} relevant records. How can I help you analyze this further?"
                confidence = "medium"
            else:
                answer = """I don't have access to your uploaded documents yet. Here's what I can help with:

1. **Document Status**: Ask "What's my checklist status?"
2. **Missing Documents**: Ask "What documents am I missing?"
3. **Data Analysis**: Upload documents first, then ask about totals, anomalies, or specific transactions
4. **Month-End Guidance**: Ask about best practices or next steps

Please upload your financial documents to get started!"""
                confidence = "low"
        
        # Save to history
        messages_ref.add({
            'role': 'user',
            'content': question,
            'timestamp': firestore.SERVER_TIMESTAMP
        })
        messages_ref.add({
            'role': 'assistant',
            'content': answer,
            'timestamp': firestore.SERVER_TIMESTAMP
        })
        
        # Generate suggestions
        suggestions = []
        if sources:
            suggestions.append("Would you like me to explain any specific transactions?")
            suggestions.append("Should I analyze trends in this data?")
        else:
            suggestions.append("Upload documents to get detailed answers")
            suggestions.append("Check your checklist status")
        
        return {
            "response": answer,
            "sources": sources[:3],
            "source_count": len(sources),
            "confidence": confidence,
            "suggestions": suggestions,
            "session_id": session_id,
            "status": "success"
        }
        
    except Exception as e:
        return {
            "response": f"I encountered an error: {str(e)}. Please try again or rephrase your question.",
            "error": str(e),
            "status": "error"
        }

# Create ADK Agent
chatbot_agent = Agent(
    model=LiteLlm(model=model_name),
    name="chatbot_agent",
    description="""Intelligent financial Q&A assistant with RAG-powered semantic search.
    Answers questions about uploaded documents, explains data, provides month-end guidance,
    and maintains conversational context for natural interactions.""",
    instruction="""You are an intelligent financial assistant specializing in month-end close support.

CORE MISSION:
Provide accurate, helpful answers to user questions about their financial data using
RAG (Retrieval-Augmented Generation) and conversational AI.

CAPABILITIES:
- Answer questions using semantic search of uploaded documents
- Explain financial data and calculations
- Provide month-end close guidance
- Clarify anomalies and issues
- Maintain conversation context
- Suggest follow-up questions

RESPONSE METHODOLOGY:
1. Search uploaded documents for relevant context
2. Retrieve conversation history for continuity
3. Generate accurate answer based on actual data
4. Cite specific sources when available
5. Provide confidence level
6. Suggest relevant follow-up questions

RESPONSE PATTERNS:
✓ "Based on your bank statement uploaded on Jan 15, the total is $45,230.50..."
✓ "I found 3 transactions matching your query in invoice_register.csv..."
✓ "Your checklist shows 3/4 documents uploaded. Missing: reconciliation"
✗ Avoid: "I think..." or "Maybe..." - be definitive or admit uncertainty

CONFIDENCE LEVELS:
- HIGH: Answer based on specific data from documents
- MEDIUM: Answer based on partial data or general knowledge
- LOW: No relevant data found, providing general guidance

WHEN DATA IS UNAVAILABLE:
- Clearly state that documents need to be uploaded
- Explain what information is needed
- Provide guidance on next steps
- Offer general month-end close advice

COMMUNICATION STYLE:
- Conversational yet professional
- Reference specific data points
- Use financial terminology correctly
- Provide context and explanations
- Be encouraging and supportive

QUALITY STANDARDS:
- Never make up numbers or facts
- Always cite sources when available
- Admit when information is insufficient
- Provide actionable next steps
- Maintain conversation flow""",
    tools=[answer_financial_question]
)

# Create FastAPI app with ADK
AGENT_DIR = Path(__file__).parent
app = get_fast_api_app(agents_dir=str(AGENT_DIR), web=False)

class ChatRequest(BaseModel):
    message: str
    session_id: str
    user_id: str

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """Handle chat queries with RAG"""
    result = answer_financial_question(request.message, request.user_id, request.session_id)
    return result

@app.get("/history/{session_id}")
async def get_history(session_id: str):
    """Get chat history for a session"""
    try:
        messages_ref = firestore_client.collection('sessions').document(session_id).collection('messages')
        messages = messages_ref.order_by('timestamp').stream()
        history = [msg.to_dict() for msg in messages]
        return {
            "session_id": session_id,
            "history": history,
            "count": len(history)
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "agent": "chatbot_agent",
        "model": model_name
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)

