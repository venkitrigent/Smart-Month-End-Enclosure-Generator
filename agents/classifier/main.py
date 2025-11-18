"""
Classifier Agent - Document Type Classification Microservice
Powered by Google ADK and Azure OpenAI
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.cli.fast_api import get_fast_api_app
import re

# Load environment variables
load_dotenv()

# Configure Azure OpenAI for LiteLLM
if os.getenv("AZURE_OPENAI_API_KEY"):
    model_name = f"vertex_ai/gemini-2.0-flash-exp"
else:
    model_name = f"vertex_ai/{os.getenv('GEMINI_MODEL', 'gemini-2.0-flash-exp')}"

# Classification tool
def classify_financial_document(filename: str, sample_content: str = None) -> dict:
    """
    Classify financial document type using pattern matching and AI.
    
    Analyzes filename and optional content sample to determine document type
    for month-end close workflows.
    
    Args:
        filename: Name of the uploaded file (e.g., "bank_statement_jan.csv")
        sample_content: Optional first few lines of file content
        
    Returns:
        Dictionary with doc_type, confidence, reasoning, and recommendations
        
    Example:
        classify_financial_document("invoice_register.csv")
        -> {
            "doc_type": "invoice_register",
            "confidence": 0.95,
            "reasoning": "Filename contains 'invoice' and 'register' keywords",
            "recommendations": "Ensure columns include invoice_number, amount, date"
        }
    """
    import re
    
    patterns = {
        "bank_statement": r"(bank|statement|account|transaction)",
        "invoice_register": r"(invoice.*register|register.*invoice)",
        "invoice": r"(invoice|bill|receipt)",
        "general_ledger": r"(ledger|journal|entry|gl)",
        "trial_balance": r"(trial|balance)",
        "reconciliation": r"(recon|reconciliation)",
        "cash_flow": r"(cash.*flow|flow.*cash)",
        "schedule": r"(schedule|depreciation|accrual)"
    }
    
    filename_lower = filename.lower()
    
    # Pattern matching
    for doc_type, pattern in patterns.items():
        if re.search(pattern, filename_lower):
            return {
                "doc_type": doc_type,
                "confidence": 0.95,
                "method": "pattern_matching",
                "reasoning": f"Filename matches pattern for {doc_type.replace('_', ' ')}",
                "recommendations": f"Verify that this is indeed a {doc_type.replace('_', ' ')} document"
            }
    
    # Fallback to AI classification if available
    if sample_content and os.getenv("AZURE_OPENAI_API_KEY"):
        try:
            from openai import AzureOpenAI
            client = AzureOpenAI(
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
            )
            
            response = client.chat.completions.create(
                model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
                messages=[
                    {"role": "system", "content": "You are a financial document classifier. Classify documents into: bank_statement, invoice_register, general_ledger, trial_balance, reconciliation, cash_flow, or other."},
                    {"role": "user", "content": f"Classify this document:\nFilename: {filename}\nContent sample: {sample_content[:500]}"}
                ],
                temperature=0.1,
                max_tokens=100
            )
            
            ai_type = response.choices[0].message.content.strip().lower()
            return {
                "doc_type": ai_type,
                "confidence": 0.85,
                "method": "ai_classification",
                "reasoning": "AI analysis of filename and content",
                "recommendations": "Review classification accuracy"
            }
        except Exception as e:
            print(f"AI classification failed: {e}")
    
    return {
        "doc_type": "unknown",
        "confidence": 0.5,
        "method": "fallback",
        "reasoning": "Could not determine document type from filename or content",
        "recommendations": "Please rename file with descriptive name or provide more context"
    }

# Create ADK Agent
classifier_agent = Agent(
    model=LiteLlm(model=model_name),
    name="classifier_agent",
    description="""Expert financial document classifier specializing in month-end close workflows.
    Identifies document types (bank statements, invoices, ledgers, reconciliations) with high accuracy
    using pattern matching and AI-powered content analysis.""",
    instruction="""You are a specialized document classification agent for financial month-end close processes.

CORE MISSION:
Accurately classify uploaded financial documents to enable proper routing and processing in the month-end workflow.

CLASSIFICATION CATEGORIES:
- bank_statement: Bank account transactions and balances
- invoice_register: List of invoices (AP/AR)
- general_ledger: Complete accounting entries
- trial_balance: Account balances summary
- reconciliation: Bank or account reconciliation reports
- cash_flow: Cash flow statements
- schedule: Supporting schedules (depreciation, accruals)
- other: Unrecognized document types

CLASSIFICATION METHODOLOGY:
1. Analyze filename for keywords and patterns
2. If available, examine content structure and headers
3. Use AI reasoning for ambiguous cases
4. Provide confidence score and reasoning
5. Suggest verification steps

OUTPUT REQUIREMENTS:
- doc_type: One of the categories above
- confidence: 0.0 to 1.0 (be honest about uncertainty)
- reasoning: Clear explanation of classification logic
- recommendations: Next steps for user

QUALITY STANDARDS:
- Prioritize accuracy over speed
- Flag ambiguous cases with lower confidence
- Provide actionable recommendations
- Never guess - use "unknown" if uncertain

COMMUNICATION STYLE:
- Professional and precise
- Clear reasoning
- Helpful recommendations""",
    tools=[classify_financial_document]
)

# Create FastAPI app with ADK
AGENT_DIR = Path(__file__).parent
app = get_fast_api_app(agents_dir=str(AGENT_DIR), web=False)

@app.post("/classify")
async def classify_endpoint(file: UploadFile = File(...)):
    """Classify uploaded financial document"""
    try:
        # Read sample content
        content = await file.read()
        sample = content.decode('utf-8')[:1000] if content else None
        
        # Classify using tool
        result = classify_financial_document(file.filename, sample)
        
        return {
            "status": "success",
            "filename": file.filename,
            **result
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "filename": file.filename
        }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "agent": "classifier_agent",
        "model": model_name
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
