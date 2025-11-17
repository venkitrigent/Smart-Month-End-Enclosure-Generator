from fastapi import FastAPI, UploadFile, File
import re

app = FastAPI(title="Classifier Agent")

DOC_PATTERNS = {
    "bank_statement": r"(bank|statement|account)",
    "invoice": r"(invoice|bill|receipt)",
    "ledger": r"(ledger|journal|entry)",
    "reconciliation": r"(recon|reconciliation)",
    "schedule": r"(schedule|depreciation|accrual)"
}

@app.post("/classify")
async def classify_document(file: UploadFile = File(...)):
    """Classify document based on filename heuristics"""
    
    filename = file.filename.lower()
    
    # Filename-based classification
    for doc_type, pattern in DOC_PATTERNS.items():
        if re.search(pattern, filename):
            return {
                "filename": file.filename,
                "doc_type": doc_type,
                "confidence": 0.9,
                "method": "filename_heuristic"
            }
    
    # Default to unknown
    return {
        "filename": file.filename,
        "doc_type": "unknown",
        "confidence": 0.5,
        "method": "default"
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}
