"""
Extractor Agent - CSV Data Extraction and Processing Microservice
Powered by Google ADK and Azure OpenAI
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, Form
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.cli.fast_api import get_fast_api_app
import pandas as pd
import io
import uuid
from typing import Dict, Any, List

# Load environment variables
load_dotenv()

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

# Configure Azure OpenAI for LiteLLM
if os.getenv("AZURE_OPENAI_API_KEY"):
    os.environ["AZURE_API_KEY"] = os.getenv("AZURE_OPENAI_API_KEY")
    os.environ["AZURE_API_BASE"] = os.getenv("AZURE_OPENAI_ENDPOINT")
    os.environ["AZURE_API_VERSION"] = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
    model_name = f"azure/{os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4o')}"
else:
    model_name = f"vertex_ai/gemini-2.0-flash-exp"

# Extraction tool
def extract_and_process_csv(csv_content: str, doc_type: str, document_id: str = None) -> Dict[str, Any]:
    """
    Extract, parse, and validate CSV financial data.
    
    Performs intelligent CSV parsing with data quality checks, column validation,
    and preparation for storage and embedding generation.
    
    Args:
        csv_content: Raw CSV file content as string
        doc_type: Document type from classification
        document_id: Unique identifier (auto-generated if not provided)
        
    Returns:
        Dictionary with:
        - document_id: Unique identifier
        - row_count: Number of rows processed
        - columns: List of column names
        - data_quality_score: 0-100 quality assessment
        - sample_rows: First 5 rows for preview
        - validation_results: Data quality checks
        - recommendations: Processing suggestions
        
    Example:
        extract_and_process_csv(csv_data, "bank_statement", "doc-123")
        -> {
            "document_id": "doc-123",
            "row_count": 150,
            "columns": ["date", "description", "amount"],
            "data_quality_score": 95,
            "validation_results": {...}
        }
    """
    try:
        # Parse CSV
        df = pd.read_csv(io.StringIO(csv_content))
        
        if not document_id:
            document_id = str(uuid.uuid4())
        
        # Data quality checks
        validation_results = {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "missing_values": df.isnull().sum().to_dict(),
            "duplicate_rows": df.duplicated().sum(),
            "empty_columns": [col for col in df.columns if df[col].isnull().all()],
            "data_types": df.dtypes.astype(str).to_dict()
        }
        
        # Calculate quality score
        quality_score = 100
        quality_score -= min(30, (df.isnull().sum().sum() / (len(df) * len(df.columns)) * 100))
        quality_score -= min(20, (validation_results["duplicate_rows"] / len(df) * 100))
        quality_score -= len(validation_results["empty_columns"]) * 10
        quality_score = max(0, quality_score)
        
        # Generate recommendations
        recommendations = []
        if validation_results["duplicate_rows"] > 0:
            recommendations.append(f"Remove {validation_results['duplicate_rows']} duplicate rows")
        if validation_results["empty_columns"]:
            recommendations.append(f"Remove empty columns: {', '.join(validation_results['empty_columns'])}")
        if df.isnull().sum().sum() > 0:
            recommendations.append("Fill or handle missing values")
        if quality_score >= 90:
            recommendations.append("Data quality is excellent - ready for processing")
        
        # Convert to records
        data_rows = df.head(100).to_dict('records')  # Limit for performance
        
        return {
            "document_id": document_id,
            "doc_type": doc_type,
            "row_count": len(df),
            "columns": list(df.columns),
            "data_quality_score": round(quality_score, 1),
            "sample_rows": df.head(5).to_dict('records'),
            "validation_results": validation_results,
            "recommendations": recommendations,
            "status": "extracted",
            "data_rows": data_rows  # For storage
        }
    except Exception as e:
        return {
            "error": str(e),
            "status": "failed",
            "recommendations": ["Check CSV format", "Ensure proper encoding", "Verify column headers"]
        }

# Create ADK Agent
extractor_agent = Agent(
    model=LiteLlm(model=model_name),
    name="extractor_agent",
    description="""Expert CSV data extraction agent for financial documents.
    Parses, validates, and prepares financial data for storage and analysis with
    comprehensive quality checks and intelligent recommendations.""",
    instruction="""You are a specialized data extraction agent for financial month-end close workflows.

CORE MISSION:
Extract, validate, and prepare financial data from CSV files for downstream processing,
ensuring data quality and completeness.

EXTRACTION PROCESS:
1. Parse CSV with intelligent encoding detection
2. Validate data structure and completeness
3. Perform quality checks (missing values, duplicates, data types)
4. Calculate data quality score (0-100)
5. Generate actionable recommendations
6. Prepare data for storage and embedding

DATA QUALITY CHECKS:
- Missing values detection and quantification
- Duplicate row identification
- Empty column detection
- Data type validation
- Row/column count verification
- Format consistency checks

QUALITY SCORING:
- 90-100: Excellent - Ready for processing
- 70-89: Good - Minor issues to address
- 50-69: Fair - Significant issues present
- <50: Poor - Major data quality problems

OUTPUT REQUIREMENTS:
- document_id: Unique identifier for tracking
- row_count: Total rows processed
- columns: List of all column names
- data_quality_score: Numerical quality assessment
- validation_results: Detailed quality metrics
- recommendations: Specific actions to improve data
- sample_rows: Preview of data

RECOMMENDATIONS STYLE:
- Specific and actionable
- Prioritized by impact
- Clear next steps
- Professional tone

ERROR HANDLING:
- Graceful failure with clear error messages
- Suggest fixes for common issues
- Never lose data silently""",
    tools=[extract_and_process_csv]
)

# Create FastAPI app with ADK
AGENT_DIR = Path(__file__).parent
app = get_fast_api_app(agents_dir=str(AGENT_DIR), web=False)

@app.post("/extract")
async def extract_endpoint(
    file: UploadFile = File(...),
    doc_type: str = Form(...),
    document_id: str = Form(None)
):
    """Extract and process CSV data"""
    try:
        content = await file.read()
        csv_content = content.decode('utf-8')
        
        result = extract_and_process_csv(csv_content, doc_type, document_id)
        
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
        "agent": "extractor_agent",
        "model": model_name
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
