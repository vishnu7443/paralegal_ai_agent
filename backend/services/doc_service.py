import uuid
import logging
from datetime import datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.db.database import Document, AnalysisJob

logger = logging.getLogger(__name__)

async def create_document(db: AsyncSession, filename: str, content_text: str) -> Document:
    """Creates a new Document record in the database."""
    db_doc = Document(filename=filename, content_text=content_text)
    db.add(db_doc)
    await db.flush()  # Populates db_doc.id
    await db.commit()
    logger.info(f"Saved document to DB: {filename} (ID: {db_doc.id})")
    return db_doc

async def get_document_by_id(db: AsyncSession, doc_id: int) -> Optional[Document]:
    """Retrieves a document by its integer ID."""
    query = select(Document).where(Document.id == doc_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def create_analysis_job(db: AsyncSession, document_id: int) -> AnalysisJob:
    """Creates a new PENDING AnalysisJob record for a document."""
    job_id = str(uuid.uuid4())
    db_job = AnalysisJob(
        id=job_id,
        document_id=document_id,
        status="PENDING",
        created_at=datetime.utcnow()
    )
    db.add(db_job)
    await db.commit()
    
    # Reload to ensure relationships are available
    query = select(AnalysisJob).where(AnalysisJob.id == job_id)
    result = await db.execute(query)
    logger.info(f"Created analysis job {job_id} for document ID {document_id}")
    return result.scalar_one()

async def update_analysis_job(
    db: AsyncSession,
    job_id: str,
    status: str,
    risk_score: Optional[float] = None,
    report_markdown: Optional[str] = None
) -> Optional[AnalysisJob]:
    """Updates status, risk score, and report markdown of an analysis job."""
    query = select(AnalysisJob).where(AnalysisJob.id == job_id)
    result = await db.execute(query)
    job = result.scalar_one_or_none()
    
    if not job:
        logger.warning(f"AnalysisJob {job_id} not found for update.")
        return None
        
    job.status = status
    if risk_score is not None:
        job.risk_score = risk_score
    if report_markdown is not None:
        job.report_markdown = report_markdown
        
    if status in ["COMPLETED", "FAILED"]:
        job.completed_at = datetime.utcnow()
        
    await db.commit()
    logger.info(f"Updated job {job_id} to status: {status}")
    return job

async def get_job_by_id(db: AsyncSession, job_id: str) -> Optional[AnalysisJob]:
    """Retrieves an analysis job by its UUID string."""
    query = select(AnalysisJob).where(AnalysisJob.id == job_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def get_all_jobs(db: AsyncSession) -> List[AnalysisJob]:
    """Retrieves all analysis jobs sorted by creation date descending."""
    query = select(AnalysisJob).order_by(AnalysisJob.created_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())
