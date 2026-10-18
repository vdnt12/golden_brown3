import os
import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from app.core.config import settings
from app.models.document import DocumentUploadResponse
from app.services.document_service import document_service
from app.core.logging import log_event

router = APIRouter()

@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_200_OK)
async def upload_document(file: UploadFile = File(...)):
    """Section 25: POST /api/upload -> multipart/form-data."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename missing.")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in {".pdf", ".txt"}:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Please upload a PDF or TXT file."
        )

    # Register document
    doc_meta = document_service.create_document(file.filename)
    safe_filename = f"{doc_meta.document_id}_{Path(file.filename).name}"
    save_path = settings.UPLOAD_DIR / safe_filename

    # Save uploaded file
    try:
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {exc}")

    # Validate file size
    file_size_mb = os.path.getsize(save_path) / (1024 * 1024)
    if file_size_mb == 0:
        save_path.unlink(missing_ok=True)
        document_service.delete_document(doc_meta.document_id)
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")

    if file_size_mb > settings.MAX_FILE_SIZE_MB:
        save_path.unlink(missing_ok=True)
        document_service.delete_document(doc_meta.document_id)
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB} MB."
        )

    log_event("UPLOAD", f"Received: {file.filename} ({file_size_mb:.2f} MB)")

    # Execute ingestion (sync or async)
    document_service.process_document(doc_meta.document_id, save_path, file.filename)

    # Check status
    updated = document_service.get_document(doc_meta.document_id)
    if updated and updated.status == "failed":
        raise HTTPException(status_code=400, detail=updated.error or "Document processing failed.")

    return DocumentUploadResponse(
        document_id=doc_meta.document_id,
        filename=file.filename,
        status=updated.status if updated else "processing",
    )
