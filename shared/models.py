from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class FileUpload(BaseModel):
    filename: str
    file_type: str
    upload_time: datetime
    user_id: str

class DocumentClassification(BaseModel):
    filename: str
    doc_type: str  # bank_statement, invoice, ledger, reconciliation
    confidence: float

class ExtractedData(BaseModel):
    filename: str
    doc_type: str
    rows: List[Dict[str, Any]]
    columns: List[str]
    row_count: int

class ChecklistItem(BaseModel):
    item_name: str
    required: bool
    status: str  # missing, uploaded, validated
    doc_type: str

class AnalyticsResult(BaseModel):
    total_transactions: int
    total_amount: float
    anomalies: List[Dict[str, Any]]
    trends: Dict[str, Any]

class ChatMessage(BaseModel):
    session_id: str
    user_id: str
    message: str
    timestamp: datetime

class ChatResponse(BaseModel):
    response: str
    context: Optional[List[Dict[str, Any]]]
    timestamp: datetime
