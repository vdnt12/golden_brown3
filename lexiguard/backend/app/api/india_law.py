"""API endpoints for Open India Law primary datasets and statutory compliance auditing.

Directly implements research and compliance features for GBDoc.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request, status

from app.api._deps import map_data_error, settings_of
from app.services import open_india_law
from app.services.lifecycle import InvalidDocumentId
from app.store import sentences as sentences_store
from app.store.repo import DocumentNotFound, open_document

router = APIRouter()


@router.get("/api/india-law/enactments")
def list_enactments() -> dict[str, Any]:
    """List all primary Indian enactments in the Open India Law dataset."""
    return {"enactments": open_india_law.get_all_enactments()}


@router.get("/api/india-law/sections")
def list_sections() -> dict[str, Any]:
    """List all statutory sections with full text, official gazette references, and keywords."""
    return {"sections": open_india_law.get_all_sections()}


@router.get("/api/india-law/judgments")
def list_judgments() -> dict[str, Any]:
    """List landmark Supreme Court and High Court judgments with ratio decidendi and official citations."""
    return {"judgments": open_india_law.get_all_judgments()}


@router.get("/api/india-law/search")
def search_law(
    q: str = Query(..., min_length=2, max_length=200, description="Legal search term or section"),
    limit: int = Query(6, ge=1, le=20),
) -> dict[str, Any]:
    """Search across enactments, statutory sections, and Supreme Court precedent library."""
    return open_india_law.search_primary_law(q, limit=limit)


@router.post("/api/documents/{document_id}/compliance-audit")
def audit_document_compliance(
    document_id: str,
    request: Request,
) -> dict[str, Any]:
    """Cross-references the uploaded contract against Indian primary law and judicial precedent.

    Audits non-compete clauses (S.27), covenants not to sue (S.28), penalty & deposit forfeiture (S.74),
    tenure & registration mandate (S.17 Reg Act & S.55 MRCA), and license revocability (S.60 Easements Act).
    """
    settings = settings_of(request)
    try:
        with open_document(settings.data_dir, document_id) as handle:
            doc = handle.connection.execute(
                "SELECT source_filename, page_count FROM document WHERE doc_id = ?",
                (document_id,),
            ).fetchone()
            if doc is None:
                raise DocumentNotFound(f"Document {document_id} not found")

            # Reconstruct document text from verified sentence store
            rows = sentences_store.all_sentences(handle.connection, document_id)
            doc_text = " ".join(r["text"] for r in rows)

            findings = open_india_law.audit_contract_compliance(doc_text)
            serialized_findings = [open_india_law.asdict(f) for f in findings]

            return {
                "document_id": document_id,
                "document_name": doc["source_filename"] or "Document",
                "page_count": int(doc["page_count"]),
                "audit_findings": serialized_findings,
                "total_rules_evaluated": len(serialized_findings),
                "high_risk_count": sum(1 for f in findings if f.risk_level == "HIGH"),
                "medium_risk_count": sum(1 for f in findings if f.risk_level == "MEDIUM"),
                "compliant_count": sum(1 for f in findings if f.risk_level == "LOW"),
            }
    except (DocumentNotFound, LookupError, FileNotFoundError, InvalidDocumentId) as exc:
        raise map_data_error(exc) from exc
