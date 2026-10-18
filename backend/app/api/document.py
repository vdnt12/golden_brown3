from fastapi import APIRouter, HTTPException, status
from app.models.document import DocumentStatusResponse
from app.services.document_service import document_service

router = APIRouter()

@router.get("/document/{document_id}/status", response_model=DocumentStatusResponse)
def get_document_status(document_id: str):
    """Section 25: GET /api/document/{document_id}/status."""
    doc = document_service.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    return DocumentStatusResponse(
        document_id=doc.document_id,
        filename=doc.filename,
        status=doc.status,
        pages=doc.pages,
        chunks=doc.chunks,
        error=doc.error,
    )

@router.delete("/document/{document_id}")
def delete_document(document_id: str):
    """Section 25: DELETE /api/document/{document_id}."""
    doc = document_service.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    document_service.delete_document(document_id)
    return {"success": True}

from app.models.document import SummarizeRequest, SummarizeResponse
from app.services.summarization_service import summarization_service

@router.post("/document/{document_id}/summarize", response_model=SummarizeResponse)
@router.post("/documents/{document_id}/summarize", response_model=SummarizeResponse)
def summarize_document(document_id: str, payload: Optional[SummarizeRequest] = None):
    """Section 15 & 23: Dedicated full-document summarization endpoint."""
    doc = document_service.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    if doc.status != "ready":
        raise HTTPException(
            status_code=400,
            detail="Document is not ready yet. Please wait until processing finishes.",
        )

    res = summarization_service.summarize_document(document_id)
    if res.get("status") == "error":
        raise HTTPException(
            status_code=500,
            detail=res.get("message", "Unable to generate document summary."),
        )

    return SummarizeResponse(
        document_id=res["document_id"],
        summary=res["summary"],
        status=res.get("status", "complete"),
        total_chunks_processed=res.get("total_chunks_processed"),
    )

