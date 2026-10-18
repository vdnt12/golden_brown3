"""The acceptance flow: upload -> map -> ask -> review -> delete.

Runs with no model and no OCR, which is the honest offline case: the ask route
must return ERROR_LOCAL_MODEL_UNAVAILABLE and never fabricate an answer.
"""
from __future__ import annotations

import pathlib

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app

FIXTURES = pathlib.Path(__file__).resolve().parents[2] / "fixtures"
ORIGIN = {"Origin": "http://127.0.0.1:8765"}


@pytest.fixture()
def client(tmp_path: pathlib.Path):
    app = create_app(
        Settings(data_dir=tmp_path, launch_code_ttl_s=3600)
    )
    test_client = TestClient(app, base_url="http://127.0.0.1:8765")
    code = app.state.launch_code
    response = test_client.post("/api/session", json={"launch_code": code}, headers=ORIGIN)
    assert response.status_code == 200
    token = response.json()["access_token"]
    test_client.headers.update({"Authorization": f"Bearer {token}", **ORIGIN})
    return test_client


def _upload(client: TestClient, name: str) -> dict:
    data = (FIXTURES / name).read_bytes()
    kind = "application/pdf" if name.endswith(".pdf") else "text/plain"
    response = client.post("/api/documents", files={"file": (name, data, kind)})
    assert response.status_code == 201, response.text
    return response.json()


def test_state_changing_requests_require_origin(client: TestClient):
    response = client.post(
        "/api/documents",
        files={"file": ("x.txt", b"hello", "text/plain")},
        headers={"Origin": "http://evil.example"},
    )
    assert response.status_code == 403


def test_full_flow_txt(client: TestClient):
    summary = _upload(client, "synthetic_rental_simple.txt")
    doc_id = summary["document_id"]
    assert summary["page_count"] >= 1
    # v3.2 upload contract
    assert len(summary["document_hash"]) == 64
    assert summary["status"] == "READY"
    metrics = summary["quality_metrics"]
    assert metrics["pages_read"] == summary["page_count"]
    assert metrics["ocr_used"] is False
    assert metrics["language_detected"] == "en"
    assert 0.0 <= metrics["garble_ratio"] <= 1.0
    assert metrics["hidden_text_detected"] is False
    assert isinstance(summary["extraction_warnings"], list)
    assert summary["created_at"]

    listing = client.get("/api/documents").json()["documents"]
    assert [item["document_id"] for item in listing] == [doc_id]

    overview = client.get(f"/api/documents/{doc_id}/overview")
    assert overview.status_code == 200
    cards = overview.json()["cards"]
    assert isinstance(cards, dict)
    assert set(cards) == {
        "Parties",
        "Term",
        "Rent",
        "Deposit",
        "Notice",
        "Lock-in",
        "Penalties",
        "Restrictions",
        "Maintenance",
        "Pets",
        "Disputes",
    }
    rent = cards["Rent"]
    assert rent["status"] == "FOUND"
    assert rent["evidence"]
    for card in cards.values():
        assert set(card) >= {"status", "summary", "evidence"}

    page = client.get(f"/api/documents/{doc_id}/pages/1")
    assert page.status_code == 200
    page_body = page.json()
    assert page_body["page_number"] == 1
    assert page_body["is_virtual_page"] is True  # .txt has no physical page
    assert page_body["ocr_used"] is False
    sentences = page_body["sentences"]
    assert sentences and sentences[0]["sid"].startswith("s_")
    first = sentences[0]
    assert page_body["text"][first["start_offset"] : first["end_offset"]] == first["text"]

    review = client.post(f"/api/documents/{doc_id}/review")
    assert review.status_code == 200
    body = review.json()
    assert body["document"]["document_id"] == doc_id
    assert body["review_status"] in {"CLEAR", "ATTENTION", "NOT_ASSESSED"}
    assert isinstance(body["attention_first"], list)
    priorities = [item["priority"] for item in body["attention_first"]]
    assert priorities == sorted(priorities)
    for item in body["attention_first"]:
        assert item["citations"], "every review item must cite a passage"
        assert set(item) >= {"category", "priority", "title", "reason", "citations"}
    for question in body["questions_for_professional"]:
        assert set(question) == {"topic", "prompt"}

    evidence = client.get(f"/api/documents/{doc_id}/evidence/{sentences[0]['sid']}")
    assert evidence.status_code == 200
    citation = evidence.json()
    assert citation["verbatim_text"] == sentences[0]["text"]
    assert citation["sids"] == [sentences[0]["sid"]]
    assert len(citation["document_hash"]) == 64
    assert len(citation["text_sha256"]) == 64
    assert citation["page"] == 1

    ask = client.post(
        f"/api/documents/{doc_id}/ask",
        json={"question": "What is the monthly rent?"},
    )
    assert ask.status_code == 200
    answer = ask.json()
    # No model is running in CI, so the only honest outcome is a fail-closed error.
    assert answer["status"] == "ERROR_LOCAL_MODEL_UNAVAILABLE"
    assert answer["claims"] == []
    assert answer["legal_verdict"] is None
    assert answer["run_meta"]["model_calls"] <= 1  # one attempted call, no result

    deletion = client.delete(f"/api/documents/{doc_id}")
    assert deletion.status_code == 200
    report = deletion.json()
    assert report["files_purged"] >= 2  # source + sqlite index
    assert report["database_unlinked"] is True
    assert report["canary_scan_passed"] is True
    assert report["files_purged"] > 0
    assert "not forensic erasure" in report["forensic_erasure_disclaimer"]
    assert client.get("/api/documents").json()["documents"] == []
    assert client.get(f"/api/documents/{doc_id}/overview").status_code == 404


def test_pdf_upload_renders_page_image(client: TestClient):
    summary = _upload(client, "synthetic_rental_conflict.pdf")
    doc_id = summary["document_id"]
    assert summary["source_kind"] == "pdf"
    image = client.get(f"/api/documents/{doc_id}/pages/1/image")
    assert image.status_code == 200
    assert image.headers["content-type"] == "image/png"
    assert image.content.startswith(b"\x89PNG")

    overview = client.get(f"/api/documents/{doc_id}/overview")
    assert overview.status_code == 200
    assert len(overview.json()["cards"]) == 11


def test_question_length_is_bounded(client: TestClient):
    doc_id = _upload(client, "synthetic_rental_simple.txt")["document_id"]
    response = client.post(
        f"/api/documents/{doc_id}/ask", json={"question": "x" * 501}
    )
    assert response.status_code == 422


def test_unknown_document_is_404(client: TestClient):
    assert client.get("/api/documents/deadbeef/overview").status_code == 404
    assert client.delete("/api/documents/deadbeef").status_code == 404


def test_upload_rejects_unsupported_type(client: TestClient):
    response = client.post(
        "/api/documents", files={"file": ("notes.md", b"# hello", "text/markdown")}
    )
    assert response.status_code == 422


def test_models_endpoint_lists_only_supported_local_models(client: TestClient):
    body = client.get("/api/models").json()
    aliases = {row["alias"] for row in body["models"]}
    assert aliases == {"gemma", "gemma-e2b", "hermes"}
    gemma = next(row for row in body["models"] if row["alias"] == "gemma")
    assert gemma["tag"] == "gemma4:e4b-it-q4_K_M"
    assert gemma["default"] is True
    hermes = next(row for row in body["models"] if row["alias"] == "hermes")
    assert hermes["tag"] == "hermes3:8b"
    # No Ollama in CI: every model must report unavailable rather than lie.
    assert all(row["available"] is False for row in body["models"])


def test_unknown_model_is_rejected(client: TestClient):
    doc_id = _upload(client, "synthetic_rental_simple.txt")["document_id"]
    response = client.post(
        f"/api/documents/{doc_id}/ask",
        json={"question": "What is the rent?", "model": "llama3:70b"},
    )
    assert response.status_code == 422
    assert "unsupported model" in response.json()["detail"]


def test_hermes_selection_fails_closed_when_not_installed(client: TestClient):
    doc_id = _upload(client, "synthetic_rental_simple.txt")["document_id"]
    response = client.post(
        f"/api/documents/{doc_id}/ask",
        json={"question": "What is the rent?", "model": "hermes"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ERROR_LOCAL_MODEL_UNAVAILABLE"
    assert body["claims"] == []
    assert body["run_meta"]["model_tag"] == "hermes3:8b"
    assert body["run_meta"]["model_calls"] <= 1
