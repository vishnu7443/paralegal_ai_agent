import os
import logging
import hashlib
import numpy as np
import google.generativeai as genai

logger = logging.getLogger(__name__)

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
        
        self.model_name = "models/text-embedding-004"
        self.dimension = 768
        
        # Check if we have a valid Gemini API Key
        api_key = os.getenv("GEMINI_API_KEY")
        self.use_gemini = bool(api_key and api_key != "mock_key" and api_key != "your_gemini_api_key_here")
        
        if self.use_gemini:
            logger.info(f"Initializing Embedder: Using Google Gemini API model '{self.model_name}' (Dimension: {self.dimension})")
            genai.configure(api_key=api_key)
        else:
            logger.info(f"Initializing Embedder: API key not set or mock. Using deterministic NumPy generator (Dimension: {self.dimension})")
            
        self._initialized = True

    def _generate_mock_vector(self, text: str) -> list[float]:
        """Generates a deterministic pseudorandom vector for a given text."""
        h = hashlib.sha256(text.encode('utf-8')).digest()
        seed = int.from_bytes(h[:4], byteorder='big')
        rng = np.random.default_rng(seed)
        vector = rng.standard_normal(self.dimension)
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        return vector.tolist()

    def embed_texts(self, texts: list[str]) -> list:
        """
        Generates list of embeddings for the input texts.
        """
        if not texts:
            return []
            
        # Re-check API key at runtime in case it was loaded late (e.g. from dotenv)
        if not self.use_gemini:
            api_key = os.getenv("GEMINI_API_KEY")
            if api_key and api_key != "mock_key" and api_key != "your_gemini_api_key_here":
                self.use_gemini = True
                genai.configure(api_key=api_key)
                logger.info(f"Runtime Embedder: Activating Google Gemini API model '{self.model_name}'")

        if self.use_gemini:
            try:
                logger.info(f"Generating Gemini embeddings for {len(texts)} chunks...")
                # Call Gemini API
                result = genai.embed_content(
                    model=self.model_name,
                    content=texts,
                    task_type="retrieval_document"
                )
                # API returns list of floats in 'embedding'
                return result['embedding']
            except Exception as e:
                logger.error(f"Gemini embedding API failed: {e}. Falling back to mock embeddings...")

        # Fallback to deterministic mock
        return [self._generate_mock_vector(t) for t in texts]

    def embed_query(self, query: str) -> list:
        """
        Generates embedding for a single query text.
        """
        if not query:
            return [0.0] * self.dimension
            
        if not self.use_gemini:
            api_key = os.getenv("GEMINI_API_KEY")
            if api_key and api_key != "mock_key" and api_key != "your_gemini_api_key_here":
                self.use_gemini = True
                genai.configure(api_key=api_key)
                logger.info(f"Runtime Embedder: Activating Google Gemini API model '{self.model_name}'")

        if self.use_gemini:
            try:
                result = genai.embed_content(
                    model=self.model_name,
                    content=query,
                    task_type="retrieval_query"
                )
                return result['embedding']
            except Exception as e:
                logger.error(f"Gemini query embedding failed: {e}. Falling back to mock query embedding...")

        return self._generate_mock_vector(query)

# Global singleton instance for app-wide reuse
embedder = DocumentEmbedder()

if __name__ == "__main__":
    # Test script
    logging.basicConfig(level=logging.INFO)
    e = DocumentEmbedder()
    test_texts = ["This is a legal contract.", "Termination clauses are high risk."]
    vectors = e.embed_texts(test_texts)
    print(f"Generated {len(vectors)} vectors of size {len(vectors[0])}.")
