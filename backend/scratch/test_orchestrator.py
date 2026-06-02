import os
import sys
import asyncio
import logging
import shutil

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.db import database
from backend.services.doc_service import create_document
from backend.agents.orchestrator import build_and_run_paralegal_graph

logger = logging.getLogger(__name__)

async def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    
    # 1. Initialize DB and create a document
    logger.info("Initializing database...")
    await database.init_db()
    
    async with database.SessionLocal() as db:
        doc = await create_document(db, "sample_nda.pdf", "MUTUAL NON-DISCLOSURE AGREEMENT...")
        doc_id = doc.id
        logger.info(f"Created document in DB with ID: {doc_id}")
        
    # 2. Copy the FAISS files from the previous RAG test to match this database ID
    src_faiss = "backend/db/indexes/index_sample_nda_doc.faiss"
    src_json = "backend/db/indexes/index_sample_nda_doc.json"
    dest_faiss = f"backend/db/indexes/index_{doc_id}.faiss"
    dest_json = f"backend/db/indexes/index_{doc_id}.json"
    
    if os.path.exists(src_faiss) and os.path.exists(src_json):
        logger.info(f"Copying mock index files to match DB ID: {doc_id}")
        shutil.copy(src_faiss, dest_faiss)
        shutil.copy(src_json, dest_json)
    else:
        logger.error("Mock index files from test_rag.py not found. Please run test_rag.py first.")
        return

    # 3. Run the orchestrator
    logger.info("=== STARTING ORCHESTRATOR RUN ===")
    
    def event_emitter(event):
        if "agent" in event:
            print(f"-> [SSE Log] {event['agent']} | {event['phase']} | {event['message']}")
        elif "type" in event and event["type"] == "token":
            print(event["content"], end="", flush=True)

    result = await build_and_run_paralegal_graph(
        job_id="test-job-uuid-abc",
        document_id=doc_id,
        emitter_callback=event_emitter
    )
    
    print("\n=== RUN COMPLETED ===")
    print(f"Overall Risk Score: {result.risk_score}/10")
    print(f"Total Flagged Clauses: {len(result.clauses)}")
    print(f"Logs count: {len(result.logs)}")

if __name__ == "__main__":
    asyncio.run(main())
