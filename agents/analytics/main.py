from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any
import statistics

app = FastAPI(title="Analytics Agent")

class AnalyticsRequest(BaseModel):
    data: Dict[str, Any]

@app.post("/analyze")
async def analyze_data(request: AnalyticsRequest):
    """Perform basic analytics on extracted data"""
    
    data = request.data
    sample_data = data.get("sample_data", [])
    
    if not sample_data:
        return {"error": "No data to analyze"}
    
    # Try to find numeric columns
    numeric_cols = []
    for col in data.get("columns", []):
        try:
            values = [float(row.get(col, 0)) for row in sample_data if row.get(col)]
            if values:
                numeric_cols.append({
                    "column": col,
                    "total": sum(values),
                    "average": statistics.mean(values),
                    "min": min(values),
                    "max": max(values)
                })
        except (ValueError, TypeError):
            continue
    
    # Simple anomaly detection (values > 2 std dev)
    anomalies = []
    for col_stat in numeric_cols:
        col = col_stat["column"]
        values = [float(row.get(col, 0)) for row in sample_data if row.get(col)]
        if len(values) > 2:
            mean = statistics.mean(values)
            stdev = statistics.stdev(values)
            for idx, val in enumerate(values):
                if abs(val - mean) > 2 * stdev:
                    anomalies.append({
                        "row": idx,
                        "column": col,
                        "value": val,
                        "reason": "outlier"
                    })
    
    return {
        "total_rows": data.get("row_count", 0),
        "numeric_analysis": numeric_cols,
        "anomalies": anomalies,
        "doc_type": data.get("doc_type", "unknown")
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}
