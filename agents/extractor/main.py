from fastapi import FastAPI, UploadFile, File, Form
import pandas as pd
import io

app = FastAPI(title="Extractor Agent")

@app.post("/extract")
async def extract_data(file: UploadFile = File(...), doc_type: str = Form(...)):
    """Extract and parse CSV data with column-aware chunking"""
    
    content = await file.read()
    
    try:
        # Parse CSV
        df = pd.read_csv(io.BytesIO(content))
        
        # Column-aware chunking
        chunks = []
        for idx, row in df.iterrows():
            chunk = {
                "row_id": idx,
                "chunk_text": ", ".join([f"{col}: {row[col]}" for col in df.columns]),
                "metadata": {
                    "filename": file.filename,
                    "doc_type": doc_type,
                    "columns": list(df.columns)
                }
            }
            chunks.append(chunk)
        
        return {
            "filename": file.filename,
            "doc_type": doc_type,
            "row_count": len(df),
            "columns": list(df.columns),
            "chunks": chunks[:10],  # Return first 10 for demo
            "sample_data": df.head(5).to_dict('records')
        }
    
    except Exception as e:
        return {
            "error": str(e),
            "filename": file.filename
        }

@app.get("/health")
async def health():
    return {"status": "healthy"}
