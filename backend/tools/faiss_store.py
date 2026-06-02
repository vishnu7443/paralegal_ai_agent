import os
import json
import logging
import numpy as np
import faiss

logger = logging.getLogger(__name__)

INDEX_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
    "db", "indexes"
)
os.makedirs(INDEX_DIR, exist_ok=True)

def get_index_paths(document_id: str) -> tuple[str, str]:
    """Returns the absolute paths for the FAISS index and JSON metadata files."""
    index_path = os.path.join(INDEX_DIR, f"index_{document_id}.faiss")
    meta_path = os.path.join(INDEX_DIR, f"index_{document_id}.json")
    return index_path, meta_path

def build_and_save_index(document_id: str, chunks: list[dict], embeddings: list[list[float]]) -> None:
    """
    Builds a FAISS index from vectors and saves it to disk along with chunks metadata.
    """
    if not chunks or not embeddings:
        logger.warning(f"No chunks or embeddings provided to index for document {document_id}")
        return

    index_path, meta_path = get_index_paths(document_id)
    
    # 1. Convert embeddings to float32 numpy array
    vectors = np.array(embeddings, dtype=np.float32)
    dimension = vectors.shape[1]
    
    # 2. Build index
    logger.info(f"Building FAISS IndexFlatL2 for document {document_id} (Size: {len(chunks)}, Dimension: {dimension})...")
    index = faiss.IndexFlatL2(dimension)
    index.add(vectors)
    
    # 3. Save index to disk
    faiss.write_index(index, index_path)
    logger.info(f"Saved FAISS index to {index_path}")
    
    # 4. Save metadata to disk
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved chunks metadata to {meta_path}")

def search_index(document_id: str, query_vector: list[float], k: int = 5) -> list[dict]:
    """
    Loads FAISS index for document, performs semantic search, and returns matched chunks with scores.
    """
    index_path, meta_path = get_index_paths(document_id)
    
    if not os.path.exists(index_path) or not os.path.exists(meta_path):
        raise FileNotFoundError(f"FAISS index or metadata not found for document {document_id}")
        
    # 1. Load index
    index = faiss.read_index(index_path)
    
    # 2. Load metadata
    with open(meta_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)
        
    # 3. Perform search
    query_arr = np.array([query_vector], dtype=np.float32)
    distances, indices = index.search(query_arr, k)
    
    # 4. Map results back to metadata
    results = []
    # indices[0] contains the indices of top k matching chunks
    # distances[0] contains the L2 distances (lower is better/closer)
    for dist, idx in zip(distances[0], indices[0]):
        if idx < 0 or idx >= len(chunks):
            continue
            
        chunk_meta = chunks[idx]
        
        # Convert L2 distance to a standard similarity score (e.g. cosine-like or inverse L2)
        # L2 distance is d^2. Similarity = 1 / (1 + d)
        similarity = float(1.0 / (1.0 + np.sqrt(dist)))
        
        results.append({
            "chunk_id": chunk_meta["id"],
            "text": chunk_meta["text"],
            "page_num": chunk_meta["page_num"],
            "block_num": chunk_meta["block_num"],
            "bbox": chunk_meta.get("bbox"),
            "score": similarity
        })
        
    return results

if __name__ == "__main__":
    # Test script
    logging.basicConfig(level=logging.INFO)
    doc_id = "test_doc"
    mock_chunks = [
        {"id": 0, "text": "This is a confidentiality clause about NDAs.", "page_num": 1, "block_num": 0},
        {"id": 1, "text": "This agreement may be terminated by either party on 30 days notice.", "page_num": 1, "block_num": 1},
        {"id": 2, "text": "Indemnification obligations shall survive termination.", "page_num": 2, "block_num": 0}
    ]
    mock_embeddings = [
        [0.1] * 384,
        [0.8] * 384,
        [0.9] * 384
    ]
    build_and_save_index(doc_id, mock_chunks, mock_embeddings)
    
    # Search mock query vector
    q_vec = [0.85] * 384
    matches = search_index(doc_id, q_vec, k=2)
    for m in matches:
        print(f"Match: {m['text']} (Score: {m['score']:.4f})")
