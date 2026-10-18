import io
import pathlib
from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app

ORIGIN = {"Origin": "http://127.0.0.1:8765"}

def test_cuad_endpoint_and_chatbot_fallback(tmp_path: pathlib.Path):
    app = create_app(Settings(data_dir=tmp_path, launch_code_ttl_s=3600))
    client = TestClient(app, base_url="http://127.0.0.1:8765")
    
    # Authenticate via session endpoint
    code = app.state.launch_code
    session_res = client.post("/api/session", json={"launch_code": code}, headers=ORIGIN)
    assert session_res.status_code == 200
    token = session_res.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}", **ORIGIN})

    # Upload a contract containing Governing Law, Covenant Not to Sue, and License Grant
    content = (
        "MASTER SERVICES AGREEMENT\n\n"
        "1. This Agreement shall be governed by and construed in accordance with the laws of the State of Delaware.\n\n"
        "2. Licensor hereby grants Licensee a perpetual, irrevocable, royalty-free license to use the Software.\n\n"
        "3. Each party covenants not to sue or initiate any litigation against the other party regarding prior claims.\n\n"
        "4. In no event shall either party's aggregate liability exceed the total fees paid under this Agreement.\n"
    ).encode("utf-8")

    upload_res = client.post(
        "/api/documents",
        files={"file": ("contract.txt", io.BytesIO(content), "text/plain")},
    )
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["document_id"]

    # Test CUAD endpoint
    cuad_res = client.get(f"/api/documents/{doc_id}/cuad")
    assert cuad_res.status_code == 200
    data = cuad_res.json()
    assert data["document_id"] == doc_id
    assert data["total_categories_checked"] == 41
    assert data["found_count"] >= 3

    categories_found = {f["label"]: f for f in data["findings"]}
    assert "Governing Law" in categories_found
    assert "Delaware" in categories_found["Governing Law"]["quote"]
    assert "Covenant Not to Sue" in categories_found
    assert "covenants not to sue" in categories_found["Covenant Not to Sue"]["quote"].lower()
    assert "Perpetual / Irrevocable License" in categories_found
    assert "perpetual" in categories_found["Perpetual / Irrevocable License"]["quote"].lower()
    assert "Cap on Liability" in categories_found

    # Test Chatbot ask with allow_fallback=True
    ask_res = client.post(
        f"/api/documents/{doc_id}/ask",
        json={"question": "What is the governing law of this agreement?", "allow_fallback": True},
    )
    assert ask_res.status_code == 200
    ask_data = ask_res.json()
    assert ask_data["status"] == "ANSWERED"
    assert len(ask_data["claims"]) > 0
    assert any("Delaware" in c["text"] or any("Delaware" in ev["quote"] for ev in c["evidence"]) for c in ask_data["claims"])

    # Test default ask without allow_fallback fails closed when Ollama is offline
    strict_res = client.post(
        f"/api/documents/{doc_id}/ask",
        json={"question": "What is the governing law of this agreement?", "allow_fallback": False},
    )
    assert strict_res.status_code == 200
    assert strict_res.json()["status"] == "ERROR_LOCAL_MODEL_UNAVAILABLE"
