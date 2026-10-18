import os
from typing import List, Protocol
from app.core.config import settings
from app.core.logging import log_event

class IEmbeddingProvider(Protocol):
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        ...

class ChromaDefaultEmbeddingProvider:
    """Uses ChromaDB's built-in ONNX all-MiniLM-L6-v2 embedding function."""
    def __init__(self):
        try:
            from chromadb.utils import embedding_functions
            self.fn = embedding_functions.DefaultEmbeddingFunction()
        except Exception:
            self.fn = None

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        if self.fn:
            return self.fn(texts)
        # Fallback deterministic normalized term vector representation if chromadb onnx fails
        return [self._hash_vector(t) for t in texts]

    def _hash_vector(self, text: str, dim: int = 384) -> List[float]:
        import hashlib
        import math
        vec = [0.0] * dim
        tokens = text.lower().split()
        for tok in tokens:
            h = int(hashlib.sha256(tok.encode()).hexdigest(), 16)
            idx = h % dim
            sign = 1.0 if ((h >> 8) & 1) else -1.0
            vec[idx] += sign
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [x / norm for x in vec]

class EmbeddingService:
    def __init__(self):
        provider_name = settings.EMBEDDING_PROVIDER.lower()
        if provider_name == "chroma":
            self.provider = ChromaDefaultEmbeddingProvider()
        else:
            self.provider = ChromaDefaultEmbeddingProvider()

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Section 9: Embed list of texts."""
        if not texts:
            return []
        embeddings = self.provider.get_embeddings(texts)
        log_event("EMBEDDING", f"Embeddings created: {len(embeddings)}")
        return embeddings

    def embed_query(self, query: str) -> List[float]:
        """Embed single search query."""
        results = self.provider.get_embeddings([query])
        return results[0]

embedding_service = EmbeddingService()
