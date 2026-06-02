import logging
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

def chunk_document_blocks(blocks: list[dict], chunk_size: int = 600, chunk_overlap: int = 150) -> list[dict]:
    """
    Chunks extracted PDF blocks into clause-sized pieces while retaining metadata
    (page number, block number, bounding box).
    
    If a block is smaller than chunk_size, it is kept as-is to preserve clause boundaries.
    If it is larger, it is split using RecursiveCharacterTextSplitter.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", "; ", ". ", " ", ""],
        keep_separator=True
    )
    
    chunks = []
    chunk_id_counter = 0
    
    for block in blocks:
        text = block["text"]
        page_num = block["page_num"]
        block_num = block["block_num"]
        bbox = block.get("bbox", None)
        
        # If the block is small, keep it intact to avoid cutting across clauses
        if len(text) <= chunk_size:
            chunks.append({
                "id": chunk_id_counter,
                "text": text,
                "page_num": page_num,
                "block_num": block_num,
                "bbox": bbox
            })
            chunk_id_counter += 1
        else:
            # Recursively split the block text
            sub_texts = splitter.split_text(text)
            for sub_text in sub_texts:
                sub_text = sub_text.strip()
                if sub_text:
                    chunks.append({
                        "id": chunk_id_counter,
                        "text": sub_text,
                        "page_num": page_num,
                        "block_num": block_num,
                        "bbox": bbox
                    })
                    chunk_id_counter += 1
                    
    logger.info(f"Chunked {len(blocks)} blocks into {len(chunks)} overlapping chunks.")
    return chunks

if __name__ == "__main__":
    # Test script
    logging.basicConfig(level=logging.INFO)
    mock_blocks = [
        {
            "text": "1. Confidentiality Obligations. The Receiving Party shall keep the Disclosing Party's Confidential Information strictly confidential and shall not disclose it to any third party without prior written consent. This obligation shall survive termination of this Agreement.",
            "page_num": 1,
            "block_num": 0
        },
        {
            "text": "2. Term and Termination. This Agreement shall commence on the Effective Date and continue for a period of three (3) years. Either party may terminate this Agreement for convenience upon thirty (30) days written notice to the other party.",
            "page_num": 1,
            "block_num": 1
        }
    ]
    res = chunk_document_blocks(mock_blocks, chunk_size=100, chunk_overlap=20)
    for c in res:
        print(f"Chunk {c['id']} (Page {c['page_num']}): {c['text']}")
