from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.core.config import settings
from app.models.document import DocumentChunk
from app.services.embedding_service import embedding_service
from app.core.logging import log_event

class VectorService:
    def __init__(self):
        # Persistent ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(settings.VECTOR_STORE_PATH),
            settings=ChromaSettings(anonymized_telemetry=False, is_persistent=True),
        )

    def _get_collection_name(self, document_id: str) -> str:
        # Chroma collection names must be 3-63 chars, start/end with alphanumeric
        clean_id = document_id.replace("-", "_")
        return f"doc_{clean_id}"

    def get_or_create_collection(self, document_id: str):
        col_name = self._get_collection_name(document_id)
        return self.client.get_or_create_collection(
            name=col_name,
            metadata={"document_id": document_id},
        )

    def store_chunks(self, document_id: str, chunks: List[DocumentChunk]) -> None:
        """Section 10: Store chunks with vectors and metadata isolated by document_id."""
        if not chunks:
            return

        collection = self.get_or_create_collection(document_id)
        texts = [c.text for c in chunks]
        embeddings = embedding_service.embed_texts(texts)

        ids = [c.chunk_id for c in chunks]
        metadatas = [
            {
                "document_id": c.document_id,
                "filename": c.filename,
                "page": c.page if c.page is not None else -1,
                "chunk_index": c.chunk_index,
            }
            for c in chunks
        ]

        # Chroma handles batches up to 5000
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )
        log_event("VECTOR", f"Stored: {len(chunks)} chunks in collection {collection.name}")

    def query(
        self,
        document_id: str,
        query_text: str,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """Query top K matching chunks strictly from this document's collection."""
        col_name = self._get_collection_name(document_id)
        try:
            collection = self.client.get_collection(name=col_name)
        except Exception:
            return []

        query_embedding = embedding_service.embed_query(query_text)
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, max(1, collection.count())),
            include=["documents", "metadatas", "distances"],
        )

        hits: List[Dict[str, Any]] = []
        if not results or not results["ids"] or not results["ids"][0]:
            return hits

        for i in range(len(results["ids"][0])):
            chunk_id = results["ids"][0][i]
            doc_text = results["documents"][0][i] if results["documents"] else ""
            meta = results["metadatas"][0][i] if results["metadatas"] else {}
            distance = results["distances"][0][i] if results["distances"] else 1.0

            page_val = meta.get("page")
            hits.append(
                {
                    "chunk_id": chunk_id,
                    "text": doc_text,
                    "filename": meta.get("filename", ""),
                    "page": page_val if page_val != -1 else None,
                    "chunk_index": meta.get("chunk_index", 0),
                    "distance": distance,
                    # Convert distance to normalized similarity score (0 to 1)
                    "similarity": max(0.0, 1.0 - (distance / 2.0)),
                }
            )

        return hits

    def get_all_chunks(self, document_id: str) -> List[Dict[str, Any]]:
        """Section 5: Retrieve ALL chunks belonging to this document, sorted by chunk_index."""
        col_name = self._get_collection_name(document_id)
        try:
            collection = self.client.get_collection(name=col_name)
        except Exception:
            return []

        count = collection.count()
        if count == 0:
            return []

        data = collection.get(include=["documents", "metadatas"])
        if not data or not data["ids"]:
            return []

        chunks: List[Dict[str, Any]] = []
        for i, chunk_id in enumerate(data["ids"]):
            doc_text = data["documents"][i] if data["documents"] else ""
            meta = data["metadatas"][i] if data["metadatas"] else {}
            page_val = meta.get("page")
            chunks.append(
                {
                    "chunk_id": chunk_id,
                    "text": doc_text,
                    "filename": meta.get("filename", ""),
                    "page": page_val if page_val != -1 else None,
                    "chunk_index": meta.get("chunk_index", 0),
                }
            )

        # Sort by chunk_index so original document sequence is preserved
        chunks.sort(key=lambda x: x["chunk_index"])
        return chunks

    def delete_document(self, document_id: str) -> bool:
        """Section 25: Remove vector collection for this document."""
        col_name = self._get_collection_name(document_id)
        try:
            self.client.delete_collection(name=col_name)
            log_event("VECTOR", f"Deleted collection {col_name}")
            return True
        except Exception:
            return False

vector_service = VectorService()

