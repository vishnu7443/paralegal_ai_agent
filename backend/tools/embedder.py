import os
import logging
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# Define local cache directory for the sentence-transformer models
MODEL_CACHE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
    "db", "models"
)
os.makedirs(MODEL_CACHE_DIR, exist_ok=True)

class DocumentEmbedder:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(DocumentEmbedder, cls).__new__(cls, *args, **kwargs)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        
        self.model_name = "all-MiniLM-L6-v2"
        logger.info(f"Initializing Embedder: Loading model '{self.model_name}' (Cache Dir: {MODEL_CACHE_DIR})...")
        
        # Enforce local caching in the project directory
        self.model = SentenceTransformer(self.model_name, cache_folder=MODEL_CACHE_DIR)
        self.dimension = self.model.get_sentence_embedding_dimension()
        
        logger.info(f"Model '{self.model_name}' loaded successfully. Embedding dimension: {self.dimension}")
        self._initialized = True

    def embed_texts(self, texts: list[str]) -> list:
        """
        Generates list of embeddings for the input texts.
        Returns a list of numpy arrays (or list of floats).
        """
        if not texts:
            return []
        
        logger.info(f"Generating embeddings for {len(texts)} chunks...")
        embeddings = self.model.encode(texts, show_progress_bar=False)
        return embeddings.tolist()

    def embed_query(self, query: str) -> list:
        """
        Generates embedding for a single query text.
        """
        logger.debug(f"Generating query embedding: '{query[:50]}'")
        embedding = self.model.encode(query, show_progress_bar=False)
        return embedding.tolist()

# Global singleton instance for app-wide reuse
embedder = DocumentEmbedder()

if __name__ == "__main__":
    # Test script
    logging.basicConfig(level=logging.INFO)
    e = DocumentEmbedder()
    test_texts = ["This is a legal contract.", "Termination clauses are high risk."]
    vectors = e.embed_texts(test_texts)
    print(f"Generated {len(vectors)} vectors of size {len(vectors[0])}.")
