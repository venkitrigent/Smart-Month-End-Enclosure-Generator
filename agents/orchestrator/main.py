from fastapi import FastAPI, UploadFile, File
import httpx
import os

app = FastAPI(title="Orchestrator Agent")

CLASSIFIER_URL = os.getenv('CLASSIFIER_URL', 'http://localhost:8001')
EXTRACTOR_URL = os.getenv('EXTRACTOR_URL', 'http://localhost:8002')
CHECKLIST_URL = os.getenv('CHECKLIST_URL', 'http://localhost:8003')
ANALYTICS_URL = os.getenv('ANALYTICS_URL', 'http://localhost:8004')

@app.post("/process-upload")
async def process_upload(file: UploadFile = File(...), user_id: str = "demo_user"):
    """Orchestrate the entire workflow"""
    
    content = await file.read()
    filename = file.filename
    
    # Step 1: Classify
    async with httpx.AsyncClient() as client:
        classify_response = await client.post(
            f"{CLASSIFIER_URL}/classify",
            files={"file": (filename, content)}
        )
        classification = classify_response.json()
    
    # Step 2: Extract
    async with httpx.AsyncClient() as client:
        extract_response = await client.post(
            f"{EXTRACTOR_URL}/extract",
            files={"file": (filename, content)},
            data={"doc_type": classification["doc_type"]}
        )
        extracted_data = extract_response.json()
    
    # Step 3: Update Checklist
    async with httpx.AsyncClient() as client:
        checklist_response = await client.post(
            f"{CHECKLIST_URL}/update",
            json={"doc_type": classification["doc_type"], "user_id": user_id}
        )
        checklist_status = checklist_response.json()
    
    # Step 4: Run Analytics
    async with httpx.AsyncClient() as client:
        analytics_response = await client.post(
            f"{ANALYTICS_URL}/analyze",
            json={"data": extracted_data}
        )
        analytics = analytics_response.json()
    
    return {
        "status": "success",
        "classification": classification,
        "extracted_rows": extracted_data.get("row_count", 0),
        "checklist": checklist_status,
        "analytics": analytics
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}
