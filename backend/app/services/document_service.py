import os
import shutil
import uuid
from pathlib import Path
from typing import Dict, Optional, List
from threading import Thread

from app.core.config import settings
from app.models.document import DocumentMetadata, DocumentStatusResponse
from app.services.extraction_service import ExtractionService, ExtractionError
from app.services.chunking_service import ChunkingService
from app.services.vector_service import vector_service
from app.core.logging import log_event

class DocumentService:
    def __init__(self):
        # In-memory document registry: document_id -> DocumentMetadata
        self._registry: Dict[str, DocumentMetadata] = {}

    def get_document(self, document_id: str) -> Optional[DocumentMetadata]:
        return self._registry.get(document_id)

    def list_documents(self) -> List[DocumentMetadata]:
        return list(self._registry.values())

    def create_document(self, filename: str) -> DocumentMetadata:
        """Section 11: Generate unique document ID and register document."""
        doc_id = str(uuid.uuid4())
        suffix = Path(filename).suffix.lower().replace(".", "")
        meta = DocumentMetadata(
            document_id=doc_id,
            filename=filename,
            file_type=suffix,
            status="processing",
        )
        self._registry[doc_id] = meta
        return meta

    def process_document(self, document_id: str, file_path: Path, filename: str) -> None:
        """Section 12: Ingestion pipeline."""
        meta = self.get_document(document_id)
        if not meta:
            return

        try:
            log_event("UPLOAD", f"Processing {filename} (ID: {document_id})")

            # 1. Text extraction & OCR fallback
            pages = ExtractionService.extract(file_path, filename)
            meta.pages = len(pages)

            # 2. Semantic Chunking
            chunks = ChunkingService.chunk_pages(pages, document_id, filename)
            meta.chunks = len(chunks)

            # 3. Vector Embeddings & Storage
            vector_service.store_chunks(document_id, chunks)

            # 4. Mark Ready
            meta.status = "ready"
            log_event("STATUS", f"Document READY: {filename} ({len(pages)} pages, {len(chunks)} chunks)")

        except ExtractionError as e:
            meta.status = "failed"
            meta.error = str(e)
            log_event("STATUS", f"Document FAILED: {filename} - {e}")
        except Exception as e:
            meta.status = "failed"
            meta.error = f"Processing error: {str(e)}"
            log_event("STATUS", f"Document FAILED: {filename} - {e}")

    def ingest_async(self, document_id: str, file_path: Path, filename: str) -> None:
        """Run ingestion in background thread so upload response is immediate."""
        thread = Thread(
            target=self.process_document,
            args=(document_id, file_path, filename),
            daemon=True,
        )
        thread.start()

    def delete_document(self, document_id: str) -> bool:
        """Section 25: Remove file, vectors, and metadata."""
        meta = self._registry.pop(document_id, None)
        vector_service.delete_document(document_id)

        # Remove uploaded file if it exists in uploads/
        for p in settings.UPLOAD_DIR.glob(f"{document_id}*"):
            try:
                if p.is_file():
                    p.unlink()
                elif p.is_dir():
                    shutil.rmtree(p)
            except Exception:
                pass

        log_event("STATUS", f"Document {document_id} deleted successfully.")
        return True

document_service = DocumentService()
