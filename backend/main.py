import os
import logging
from datetime import datetime
from typing import Dict, Any, List
from fastapi import FastAPI, Depends, BackgroundTasks, HTTPException, UploadFile, File, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Import database, models, schemas, and services
from backend.db import database
from backend.models.document import DocumentResponse, AnalysisJobResponse, DocumentCompareRequest
from backend.services.doc_service import (
    create_analysis_job, 
    update_analysis_job, 
    get_job_by_id, 
    get_all_jobs,
    get_document_by_id
)
from backend.services.ingest_service import ingest_pdf_pipeline
from backend.services.sse_service import sse_service
from backend.agents.orchestrator import build_and_run_paralegal_graph
from backend.tools.embedder import embedder
from backend.tools.faiss_store import search_index

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI(
    title="Agentic AI Ops Manager - Paralegal Agent Crew",
    description="Explainable multi-agent legal contract risk analysis and RAG system.",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def on_startup():
    """Initializes tables on startup with fallback to SQLite."""
    logger.info("FastAPI: Initializing database engine and tables...")
    await database.init_db()
    logger.info("FastAPI: Database initialization completed.")

# Pydantic schemas for request bodies
class AnalyzeRequest(BaseModel):
    document_id: int = Field(..., description="ID of the document to analyze")

class SearchRequest(BaseModel):
    document_id: int = Field(..., description="ID of the document to search")
    query: str = Field(..., description="Semantic search query")
    k: int = Field(5, description="Number of results to return")

# ==========================================
# Background Analysis Worker
# ==========================================

async def run_analysis_job_in_background(job_id: str, document_id: int):
    """
    Background worker running the LangGraph orchestrator.
    Emits real-time event updates to SSE and updates the database.
    """
    logger.info(f"Worker: Launching orchestrator for Job {job_id} on Document {document_id}...")
    
    async with database.SessionLocal() as db:
        try:
            # 1. Set job status to RUNNING in database
            await update_analysis_job(db, job_id=job_id, status="RUNNING")
            
            # SSE emitter callback
            def publish_agent_log(event: Dict[str, Any]):
                import asyncio
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(sse_service.publish_event(job_id, event))
            
            # 2. Execute Orchestrator Graph
            final_state = await build_and_run_paralegal_graph(
                job_id=job_id,
                document_id=document_id,
                emitter_callback=publish_agent_log
            )
            
            # 3. Save final results to DB and set status to COMPLETED
            await update_analysis_job(
                db,
                job_id=job_id,
                status="COMPLETED",
                risk_score=final_state.risk_score,
                report_markdown=final_state.report_markdown
            )
            
            # Publish final completion event to SSE
            await sse_service.publish_event(job_id, {
                "agent": "Orchestrator",
                "phase": "COMPLETE",
                "message": "Global contract risk assessment successfully completed. Data saved.",
                "timestamp": ""
            })
            
        except Exception as e:
            logger.error(f"Worker: Analysis failed for Job {job_id}: {e}", exc_info=True)
            try:
                await update_analysis_job(db, job_id=job_id, status="FAILED")
                await sse_service.publish_event(job_id, {
                    "agent": "Orchestrator",
                    "phase": "FAILED",
                    "message": f"Global failure occurred during execution: {str(e)}",
                    "timestamp": ""
                })
            except Exception as ex:
                logger.error(f"Worker: Critical failure during DB error recovery ({ex})")

# ==========================================
# REST Endpoints
# ==========================================

@app.post("/api/upload", status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(database.get_db)
):
    """
    Uploads a PDF contract file, runs the ingestion pipeline
    (parsing, chunking, embedding, indexing), and registers the document in DB.
    """
    logger.info(f"API: Received upload request for file: {file.filename}")
    if not file.filename.endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file format. Only PDF files are allowed."
        )
        
    try:
        file_bytes = await file.read()
        doc_id = await ingest_pdf_pipeline(db, file.filename, file_bytes)
        return {
            "document_id": doc_id,
            "filename": file.filename,
            "message": "Document uploaded and parsed successfully."
        }
    except Exception as e:
        logger.error(f"API: Failed to upload and ingest document: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion pipeline failed: {str(e)}"
        )

@app.post("/api/analyse", status_code=201)
async def analyze_document(
    request: AnalyzeRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(database.get_db)
):
    """
    Dispatches a background LangGraph analysis job for the given document.
    """
    logger.info(f"API: Received analysis request for Document ID: {request.document_id}")
    
    doc = await get_document_by_id(db, request.document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{request.document_id}' not found."
        )
        
    try:
        # 1. Create a database record for the job
        job = await create_analysis_job(db, request.document_id)
        
        # 2. Dispatch background worker
        background_tasks.add_task(
            run_analysis_job_in_background,
            job_id=job.id,
            document_id=request.document_id
        )
        
        logger.info(f"API: Dispatched Job {job.id} for Document {request.document_id}.")
        return {
            "job_id": job.id,
            "document_id": request.document_id,
            "status": "PENDING"
        }
    except Exception as e:
        logger.error(f"API: Failed to dispatch analysis job: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database or worker dispatch error: {str(e)}"
        )

@app.get("/api/stream/{job_id}")
async def stream_job_events(job_id: str):
    """
    Exposes a Server-Sent Events (SSE) stream for a running Analysis Job.
    Emits agent status logs and report tokens in real-time.
    """
    logger.info(f"API: SSE client connected for Job {job_id}.")
    return StreamingResponse(
        sse_service.listen_events(job_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@app.get("/api/report/{job_id}", response_model=AnalysisJobResponse)
async def get_analysis_report(job_id: str, db: AsyncSession = Depends(database.get_db)):
    """Retrieves full metadata, status, and compiled markdown report for a job."""
    job = await get_job_by_id(db, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis Job with ID '{job_id}' not found."
        )
    return job

@app.get("/api/jobs")
async def list_jobs(db: AsyncSession = Depends(database.get_db)):
    """Retrieves a list of all jobs with document metadata."""
    jobs = await get_all_jobs(db)
    return jobs

def _load_and_evaluate_clauses(document_id: int) -> List[Dict[str, Any]]:
    """Helper to load and evaluate risk clauses for a document."""
    index_meta_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 
        "db", "indexes", f"index_{document_id}.json"
    )
    
    try:
        import json
        if os.path.exists(index_meta_path):
            with open(index_meta_path, "r", encoding="utf-8") as f:
                chunks = json.load(f)
            
            from backend.agents.risk_agent import evaluate_clause_risk
            scored_clauses = []
            for chunk in chunks:
                score, category, level, explanation = evaluate_clause_risk(
                    chunk["text"], 
                    "General", 
                    0.5 # default similarity weight
                )
                if score >= 3.0:
                    scored_clauses.append({
                        "chunk_id": chunk["id"],
                        "text": chunk["text"],
                        "page_num": chunk["page_num"],
                        "block_num": chunk["block_num"],
                        "risk_score": score,
                        "risk_category": category,
                        "risk_level": level,
                        "risk_explanation": explanation
                    })
            scored_clauses.sort(key=lambda x: x["risk_score"], reverse=True)
            return scored_clauses
    except Exception as e:
        logger.error(f"Failed to load clauses for document {document_id}: {e}", exc_info=True)
        
    return []

@app.get("/api/clauses/{job_id}")
async def get_job_clauses(job_id: str, db: AsyncSession = Depends(database.get_db)):
    """
    Retrieves the extracted clauses for a job, sorted by risk score descending.
    """
    job = await get_job_by_id(db, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{job_id}' not found."
        )
        
    if job.status != "COMPLETED":
        return []
        
    return _load_and_evaluate_clauses(job.document_id)

@app.get("/api/report/{job_id}/pdf")
async def download_analysis_pdf(job_id: str, db: AsyncSession = Depends(database.get_db)):
    """
    Compiles and downloads a premium corporate risk brief PDF report.
    """
    logger.info(f"API: Received request for PDF report of Job {job_id}")
    job = await get_job_by_id(db, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis Job with ID '{job_id}' not found."
        )
        
    if job.status != "COMPLETED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Analysis is not completed yet (Current Status: {job.status})."
        )
        
    try:
        from backend.services.pdf_brief import generate_pdf_report
        
        # Load and evaluate clauses
        clauses = _load_and_evaluate_clauses(job.document_id)
        
        # Define output path
        pdf_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "exports")
        os.makedirs(pdf_dir, exist_ok=True)
        pdf_path = os.path.join(pdf_dir, f"report_{job_id}.pdf")
        
        # Generate the PDF file
        generate_pdf_report(job, clauses, pdf_path)
        
        # Verify the file is generated
        if not os.path.exists(pdf_path):
            raise FileNotFoundError("PDF file was not created by the brief service.")
            
        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename=f"Legal_Risk_Report_{job_id[:8]}.pdf"
        )
    except Exception as e:
        logger.error(f"API: Failed to generate PDF report: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF generation failed: {str(e)}"
        )

@app.post("/api/search")
async def semantic_search(request: SearchRequest):
    """
    Runs an ad-hoc semantic query against a document's FAISS index.
    """
    logger.info(f"API: Semantic search request on Document {request.document_id} for '{request.query[:50]}'")
    try:
        query_vector = embedder.embed_query(request.query)
        matches = search_index(str(request.document_id), query_vector, k=request.k)
        
        # Add risk profiling to matches in real-time
        from backend.agents.risk_agent import evaluate_clause_risk
        for m in matches:
            score, category, level, explanation = evaluate_clause_risk(m["text"], "General", m["score"])
            m["risk_score"] = score
            m["risk_category"] = category
            m["risk_level"] = level
            m["risk_explanation"] = explanation
            
        return matches
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vector store index not found for Document {request.document_id}. Ingest it first."
        )
    except Exception as e:
        logger.error(f"API: Search query failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Semantic search failed: {str(e)}"
        )

@app.post("/api/compare")
async def compare_documents(request: DocumentCompareRequest, db: AsyncSession = Depends(database.get_db)):
    """
    Compares risk levels and metrics between multiple analyzed contracts.
    """
    logger.info(f"API: Comparing jobs: {request.job_ids}")
    comparison_data = []
    
    for job_id in request.job_ids:
        job = await get_job_by_id(db, job_id)
        if not job or job.status != "COMPLETED":
            continue
            
        # Extract clauses to get details
        clauses = await get_job_clauses(job_id, db)
        
        critical_count = sum(1 for c in clauses if c["risk_score"] >= 9.0)
        high_count = sum(1 for c in clauses if 7.0 <= c["risk_score"] < 9.0)
        med_count = sum(1 for c in clauses if 4.0 <= c["risk_score"] < 7.0)
        
        comparison_data.append({
            "job_id": job.id,
            "filename": job.document.filename if job.document else "Unknown Contract",
            "risk_score": job.risk_score,
            "clause_count": len(clauses),
            "severity_breakdown": {
                "critical": critical_count,
                "high": high_count,
                "medium": med_count
            }
        })
        
    return comparison_data

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Paralegal Agent API"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
