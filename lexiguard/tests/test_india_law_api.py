import io
import pathlib
from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app

ORIGIN = {"Origin": "http://127.0.0.1:8765"}

def test_open_india_law_api_and_compliance_audit(tmp_path: pathlib.Path):
    app = create_app(Settings(data_dir=tmp_path, launch_code_ttl_s=3600))
    client = TestClient(app, base_url="http://127.0.0.1:8765")

    # Authenticate via session
    code = app.state.launch_code
    session_res = client.post("/api/session", json={"launch_code": code}, headers=ORIGIN)
    assert session_res.status_code == 200
    token = session_res.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}", **ORIGIN})

    # Test enactments list
    enact_res = client.get("/api/india-law/enactments")
    assert enact_res.status_code == 200
    enactments = enact_res.json()["enactments"]
    assert len(enactments) >= 5
    assert any("Indian Contract Act" in e["title"] for e in enactments)

    # Test sections list
    sec_res = client.get("/api/india-law/sections")
    assert sec_res.status_code == 200
    sections = sec_res.json()["sections"]
    assert any(s["section_number"] == "Section 27" for s in sections)
    assert any(s["section_number"] == "Section 74" for s in sections)

    # Test judgments list
    judg_res = client.get("/api/india-law/judgments")
    assert judg_res.status_code == 200
    judgments = judg_res.json()["judgments"]
    assert any("Zaheer Khan" in j["case_name"] for j in judgments)
    assert any("Kailash Nath" in j["case_name"] for j in judgments)

    # Test search query
    search_res = client.get("/api/india-law/search?q=restraint of trade non-compete")
    assert search_res.status_code == 200
    search_data = search_res.json()
    assert len(search_data["sections"]) > 0
    assert any("Section 27" in s["section_number"] for s in search_data["sections"])

    # Upload contract with non-compete and deposit forfeiture
    contract_content = (
        "EMPLOYMENT AND CONFIDENTIALITY AGREEMENT\n\n"
        "1. Post-Termination Covenant: Employee shall not directly or indirectly compete, solicit, or engage in "
        "any business similar to the Company for a period of 2 years after termination of this agreement.\n\n"
        "2. In the event of any breach, the Company shall forfeit the entire security deposit of Rs. 1,00,000 as penalty.\n\n"
        "3. This Agreement is executed for a term of 24 months.\n"
    ).encode("utf-8")

    upload_res = client.post(
        "/api/documents",
        files={"file": ("indian_contract.txt", io.BytesIO(contract_content), "text/plain")},
    )
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["document_id"]

    # Test compliance audit endpoint
    audit_res = client.post(f"/api/documents/{doc_id}/compliance-audit")
    assert audit_res.status_code == 200
    audit_data = audit_res.json()
    assert audit_data["document_id"] == doc_id
    assert audit_data["total_rules_evaluated"] >= 2
    assert audit_data["high_risk_count"] >= 1  # Section 27 non-compete void

    finding_rules = {f["section"]: f for f in audit_data["audit_findings"]}
    assert "Section 27" in finding_rules
    assert finding_rules["Section 27"]["compliance_status"] == "VOID_UNENFORCEABLE"
    assert "Section 74" in finding_rules

    # Test chatbot asking about Section 27 backed by Open India Law dataset
    chat_res = client.post(
        f"/api/documents/{doc_id}/ask",
        json={"question": "What does Section 27 say about non-compete agreements?", "allow_fallback": True},
    )
    assert chat_res.status_code == 200
    chat_data = chat_res.json()
    assert chat_data["status"] == "ANSWERED"
    assert any("Section 27" in c["text"] or "restrained" in c["text"].lower() for c in chat_data["claims"])
