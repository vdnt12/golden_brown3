
import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@pytest.fixture
def app_client(tmp_path):
    settings = Settings(data_dir=tmp_path / "data", port=8765)
    app = create_app(settings)
    client = TestClient(app, base_url="http://127.0.0.1:8765")
    return app, client


def test_session_bootstrap_then_health(app_client):
    app, client = app_client
    assert client.get("/api/health").status_code == 401

    code = app.state.launch_code
    response = client.post("/api/session", json={"launch_code": code})
    assert response.status_code == 200
    token = response.json()["access_token"]

    health = client.get("/api/health", headers={"Authorization": f"Bearer {token}"})
    assert health.status_code == 200
    body = health.json()
    # v3.2 health contract
    assert set(body) >= {
        "status",
        "local_model_available",
        "model_tag",
        "model_digest",
        "parser_engine",
        "storage_backend",
    }
    assert body["status"] == "degraded"  # no Ollama in CI, reported honestly
    assert body["local_model_available"] is False
    assert body["model_tag"] == "gemma4:e4b-it-q4_K_M"
    assert body["parser_engine"].startswith("pypdfium2")
    assert body["storage_backend"] == "sqlite-fts5"
    assert set(body["models"]) == {"gemma", "gemma-e2b", "hermes"}
    assert "api" not in body  # the old scalar-only payload is gone

    reused = client.post("/api/session", json={"launch_code": code})
    assert reused.status_code == 401


def test_bad_host_is_rejected(app_client):
    _, client = app_client
    response = client.get("/api/health", headers={"Host": "evil.example:8765"})
    assert response.status_code == 403


def test_bad_origin_is_rejected_on_post(app_client):
    app, client = app_client
    response = client.post(
        "/api/session",
        json={"launch_code": app.state.launch_code},
        headers={"Origin": "http://evil.example"},
    )
    assert response.status_code == 403


def test_unauthenticated_api_routes_are_blocked(app_client):
    _, client = app_client
    for path in ("/api/documents", "/api/documents/x/overview"):
        assert client.get(path).status_code == 401


def test_placeholder_index_contains_no_secret(app_client):
    app, client = app_client
    response = client.get("/")
    assert response.status_code == 200
    assert app.state.launch_code not in response.text
    assert "k=" not in response.text
