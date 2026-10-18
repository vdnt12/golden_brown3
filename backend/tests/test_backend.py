import io
import pathlib
import pytest
import pymupdf
from fastapi.testclient import TestClient

from app.main import app
from app.services.extraction_service import ExtractionService, ExtractionError
from app.services.chunking_service import ChunkingService
from app.models.document import ExtractedPage

client = TestClient(app)

def test_health_check():
    """Section 25 & 31: GET /api/health -> {'status': 'ok'}."""
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}

def test_empty_file_rejected():
    """Section 22 & 31: Empty file rejected with clear error."""
    resp = client.post(
        "/api/upload",
        files={"file": ("empty.txt", io.BytesIO(b""), "text/plain")},
    )
    assert resp.status_code == 400
    assert "empty" in resp.json()["detail"].lower()

def test_unsupported_file_rejected():
    """Section 22 & 31: Unsupported file rejected."""
    resp = client.post(
        "/api/upload",
        files={"file": ("image.png", io.BytesIO(b"fake-image"), "image/png")},
    )
    assert resp.status_code == 400
    assert "unsupported file type" in resp.json()["detail"].lower()

def test_pdf_extraction_and_chunking(tmp_path: pathlib.Path):
    """Section 5, 8 & 31: PyMuPDF extraction and semantic chunking."""
    pdf_path = tmp_path / "sample.pdf"
    doc = pymupdf.open()
    page1 = doc.new_page()
    page1.insert_text((50, 72), "CONFIDENTIAL AGREEMENT\n\n1. Scope of Work\nContractor shall build the software.")
    page2 = doc.new_page()
    page2.insert_text((50, 72), "2. Compensation\nPayment is due within 15 days of invoice submission.")
    doc.save(str(pdf_path))
    doc.close()

    pages = ExtractionService.extract_pdf(pdf_path)
    assert len(pages) == 2
    assert "Scope of Work" in pages[0].text
    assert "Payment is due" in pages[1].text

    chunks = ChunkingService.chunk_pages(pages, "doc_test_123", "sample.pdf")
    assert len(chunks) >= 2
    assert any(c.page == 1 for c in chunks)
    assert any(c.page == 2 for c in chunks)

def test_critical_e2e_section_32(tmp_path: pathlib.Path):
    """Section 32: CRITICAL END-TO-END TEST with test_document.txt."""
    content = (
        "Company Name: Golden Brown Technologies\n"
        "CEO: Rahul Sharma\n"
        "Founded: 2024\n"
        "Headquarters: Bengaluru\n"
        "Annual leave: 24 days\n"
        "Notice period: 30 days\n"
    ).encode("utf-8")

    # 1. Upload
    upload_res = client.post(
        "/api/upload",
        files={"file": ("test_document.txt", io.BytesIO(content), "text/plain")},
    )
    assert upload_res.status_code == 200
    data = upload_res.json()
    doc_id = data["document_id"]
    assert data["filename"] == "test_document.txt"
    assert data["status"] in {"ready", "processing"}

    # 2. Check Status
    status_res = client.get(f"/api/document/{doc_id}/status")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["status"] == "ready"
    assert status_data["pages"] >= 1
    assert status_data["chunks"] >= 1

    # 3. Test Questions
    # Q1: What is the company name? -> Golden Brown Technologies
    q1 = client.post("/api/chat", json={"document_id": doc_id, "question": "What is the company name?"})
    assert q1.status_code == 200
    ans1 = q1.json()["answer"]
    assert "Golden Brown Technologies" in ans1
    assert len(q1.json()["sources"]) > 0

    # Q2: Who is the CEO? -> Rahul Sharma
    q2 = client.post("/api/chat", json={"document_id": doc_id, "question": "Who is the CEO?"})
    assert q2.status_code == 200
    ans2 = q2.json()["answer"]
    assert "Rahul Sharma" in ans2

    # Q3: When was the company founded? -> 2024
    q3 = client.post("/api/chat", json={"document_id": doc_id, "question": "When was the company founded?"})
    assert q3.status_code == 200
    ans3 = q3.json()["answer"]
    assert "2024" in ans3

    # Q4: How many annual leave days are provided? -> 24 days
    q4 = client.post("/api/chat", json={"document_id": doc_id, "question": "How many annual leave days are provided?"})
    assert q4.status_code == 200
    ans4 = q4.json()["answer"]
    assert "24 days" in ans4

    # Q5: What is the notice period? -> 30 days
    q5 = client.post("/api/chat", json={"document_id": doc_id, "question": "What is the notice period?"})
    assert q5.status_code == 200
    ans5 = q5.json()["answer"]
    assert "30 days" in ans5

    # Q6: What is the company's revenue? (NOT in document) -> Must say: "I couldn't find that information in the uploaded document."
    q6 = client.post("/api/chat", json={"document_id": doc_id, "question": "What is the company's revenue?"})
    assert q6.status_code == 200
    ans6 = q6.json()["answer"]
    assert "couldn't find that information in the uploaded document" in ans6.lower()

    # 4. Delete document
    del_res = client.delete(f"/api/document/{doc_id}")
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True

    # 5. After delete -> 404
    after_res = client.get(f"/api/document/{doc_id}/status")
    assert after_res.status_code == 404

def test_full_document_summarization_section_22_23():
    """Section 22 & 23: Test case for dedicated and chat full-document summarization."""
    content = (
        "Company: Golden Brown Technologies\n"
        "Owner: Rahul Sharma\n"
        "Founded: 2024\n"
        "Location: Bengaluru\n"
        "Electricity Bill: ₹2,438\n"
        "Due Date: 15 October 2026\n"
        "Consumption: 324 units\n"
        "Account Number: GB202610001\n\n"
        "Additional Information:\n"
        "The company operates a software development center in Bengaluru.\n"
        "The electricity bill covers the September 2026 billing period.\n"
        "Payment must be made before the due date to avoid late charges.\n"
    ).encode("utf-8")

    upload_res = client.post(
        "/api/upload",
        files={"file": ("test_summary.txt", io.BytesIO(content), "text/plain")},
    )
    assert upload_res.status_code == 200
    doc_id = upload_res.json()["document_id"]

    # 1. Test dedicated API endpoint POST /api/documents/{id}/summarize
    sum_res = client.post(f"/api/documents/{doc_id}/summarize", json={"document_id": doc_id})
    assert sum_res.status_code == 200
    sum_data = sum_res.json()
    assert sum_data["status"] == "complete"
    summary = sum_data["summary"]

    required_facts = [
        "Golden Brown Technologies",
        "Rahul Sharma",
        "2024",
        "Bengaluru",
        "₹2,438",
        "15 October 2026",
        "324 units",
        "GB202610001",
        "September 2026",
    ]
    for fact in required_facts:
        assert fact.lower() in summary.lower(), f"Fact '{fact}' missing from summary!"

    # 2. Test chat intent trigger for 'Summarize the document.'
    chat_res = client.post("/api/chat", json={"document_id": doc_id, "question": "Summarize the document."})
    assert chat_res.status_code == 200
    chat_answer = chat_res.json()["answer"]
    for fact in required_facts:
        assert fact.lower() in chat_answer.lower(), f"Fact '{fact}' missing from chat summary!"

    # 3. Clean up
    client.delete(f"/api/document/{doc_id}")

