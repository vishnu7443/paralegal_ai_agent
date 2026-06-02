import os
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from backend.tools.pdf_extractor import extract_pdf_blocks
from backend.tools.chunker import chunk_document_blocks
from backend.tools.embedder import embedder
from backend.tools.faiss_store import build_and_save_index
from backend.services.doc_service import create_document

logger = logging.getLogger(__name__)

UPLOAD_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
    "exports", "documents"
)
os.makedirs(UPLOAD_DIR, exist_ok=True)

async def ingest_pdf_pipeline(db: AsyncSession, filename: str, file_bytes: bytes) -> int:
    """
    Ingests a legal PDF document:
    1. Saves the PDF file to disk.
    2. Extracts blocks of text from the PDF.
    3. Chunks the text blocks into clause-sized pieces.
    4. Generates vector embeddings for each chunk.
    5. Builds and saves a local FAISS index.
    6. Saves the Document record to the database.
    
    Returns the database ID of the ingested document.
    """
    # 1. Save file to disk
    safe_filename = filename.replace(" ", "_")
    dest_path = os.path.join(UPLOAD_DIR, safe_filename)
    logger.info(f"Saving uploaded PDF to: {dest_path}")
    with open(dest_path, "wb") as f:
        f.write(file_bytes)
        
    try:
        # 2. Extract PDF text blocks
        blocks = extract_pdf_blocks(dest_path)
        full_text = "\n\n".join([b["text"] for b in blocks])
        
        # 3. Save Document in DB to get its ID
        db_doc = await create_document(db, safe_filename, full_text)
        doc_id = str(db_doc.id)
        
        # 4. Chunk blocks
        chunks = chunk_document_blocks(blocks)
        
        # 5. Embed chunks
        texts = [c["text"] for c in chunks]
        embeddings = embedder.embed_texts(texts)
        
        # 6. Build and save local FAISS index
        build_and_save_index(doc_id, chunks, embeddings)
        
        logger.info(f"Ingestion pipeline completed successfully for document ID {doc_id} ('{safe_filename}').")
        return db_doc.id
    except Exception as e:
        logger.error(f"Failed to ingest PDF {filename}: {e}", exc_info=True)
        # Clean up file on failure
        if os.path.exists(dest_path):
            try:
                os.remove(dest_path)
            except Exception:
                pass
        raise e
