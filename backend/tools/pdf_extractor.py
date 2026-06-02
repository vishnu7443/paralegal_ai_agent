import os
import logging
import fitz  # PyMuPDF

logger = logging.getLogger(__name__)

def extract_pdf_blocks(pdf_path: str) -> list[dict]:
    """
    Extracts text blocks from a PDF file using PyMuPDF (fitz).
    Each extracted block contains:
    - text: The extracted text content
    - page_num: The 1-based page number
    - block_num: The index of the block on that page
    - bbox: bounding box coordinates of the block (x0, y0, x1, y1)
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found at: {pdf_path}")

    blocks_data = []
    try:
        logger.info(f"Extracting text blocks from: {pdf_path}")
        doc = fitz.open(pdf_path)
        
        for page_idx, page in enumerate(doc):
            page_num = page_idx + 1
            # "blocks" format: (x0, y0, x1, y1, "text", block_no, block_type)
            page_blocks = page.get_text("blocks")
            
            for b in page_blocks:
                # b[6] is block_type: 0 for text, 1 for image
                if b[6] == 0:
                    text = b[4].strip()
                    if text:
                        blocks_data.append({
                            "text": text,
                            "page_num": page_num,
                            "block_num": b[5],
                            "bbox": (b[0], b[1], b[2], b[3])
                        })
                        
        logger.info(f"Extracted {len(blocks_data)} blocks from {len(doc)} pages.")
        return blocks_data
    except Exception as e:
        logger.error(f"Error extracting PDF: {e}", exc_info=True)
        raise e

if __name__ == "__main__":
    # Test script
    import sys
    logging.basicConfig(level=logging.INFO)
    if len(sys.argv) > 1:
        test_pdf = sys.argv[1]
        try:
            res = extract_pdf_blocks(test_pdf)
            for i, b in enumerate(res[:5]):
                print(f"Block {i} (Page {b['page_num']}): {b['text'][:100]}...")
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("Please provide a test PDF path.")
