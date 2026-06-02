import os
import sys
import logging

# Ensure root of project is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.scratch.create_mock_nda import generate_mock_nda
from backend.tools.pdf_extractor import extract_pdf_blocks
from backend.tools.chunker import chunk_document_blocks
from backend.tools.embedder import embedder
from backend.tools.faiss_store import build_and_save_index, search_index

logger = logging.getLogger(__name__)

def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    
    pdf_path = "backend/scratch/sample_nda.pdf"
    doc_id = "sample_nda_doc"
    
    # 1. Generate Mock PDF
    logger.info("=== STEP 1: Generating Mock PDF ===")
    generate_mock_nda(pdf_path)
    
    # 2. Extract PDF Blocks
    logger.info("=== STEP 2: Extracting PDF Blocks ===")
    blocks = extract_pdf_blocks(pdf_path)
    for b in blocks[:2]:
        logger.info(f"Page {b['page_num']}, Block {b['block_num']}: {b['text'][:120]}...")
        
    # 3. Chunk Document Blocks
    logger.info("=== STEP 3: Chunking Document Blocks ===")
    chunks = chunk_document_blocks(blocks, chunk_size=200, chunk_overlap=50)
    for c in chunks[:3]:
        logger.info(f"Chunk {c['id']} (Page {c['page_num']}): {c['text'][:120]}...")
        
    # 4. Generate Embeddings & Save to FAISS
    logger.info("=== STEP 4: Embedding & Saving to FAISS ===")
    texts = [c["text"] for c in chunks]
    embeddings = embedder.embed_texts(texts)
    build_and_save_index(doc_id, chunks, embeddings)
    
    # 5. Search Index
    logger.info("=== STEP 5: Searching Index for 'termination' ===")
    query = "termination"
    query_vector = embedder.embed_query(query)
    matches = search_index(doc_id, query_vector, k=3)
    
    logger.info(f"Found {len(matches)} matching chunks for query '{query}':")
    for idx, m in enumerate(matches):
        print(f"\n[{idx+1}] Score: {m['score']:.4f} | Page {m['page_num']} | Block {m['block_num']}")
        print(f"Content: {m['text']}")

if __name__ == "__main__":
    main()
