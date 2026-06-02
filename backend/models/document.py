from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class DocumentResponse(BaseModel):
    id: int
    filename: str
    content_text: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class AnalysisJobResponse(BaseModel):
    id: str
    document_id: int
    status: str
    risk_score: Optional[float] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    report_markdown: Optional[str] = None
    document: Optional[DocumentResponse] = None

    class Config:
        from_attributes = True

class DocumentCompareRequest(BaseModel):
    job_ids: List[str] = Field(..., description="List of job IDs to compare")
