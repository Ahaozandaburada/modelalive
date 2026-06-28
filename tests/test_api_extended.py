"""API endpoint coverage."""

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_openapi_schema():
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert response.json()["info"]["title"] == "Model Alive"


def test_health_fields():
    data = client.get("/v1/health").json()
    assert data["status"] == "ok"
    assert data["model_count"] >= 115


def test_sources():
    data = client.get("/v1/sources").json()
    assert "anthropic" in data["sources"]


def test_alive_active():
    response = client.get("/v1/alive", params={"model": "claude-sonnet-4-6"})
    assert response.status_code == 200
    assert response.json()["status"] == "active"


def test_resolve_endpoint():
    data = client.get("/v1/resolve", params={"model": "claude-sonnet-4-20250514"}).json()
    assert data["resolved"] == "claude-sonnet-4-6"


def test_registry_filter_provider():
    data = client.get("/v1/registry", params={"provider": "google", "status": "retired"}).json()
    assert data["count"] >= 5


def test_expiring_endpoint():
    data = client.get("/v1/expiring", params={"days": 30}).json()
    assert data["count"] >= 1


def test_batch_all_active():
    response = client.post(
        "/v1/alive/batch",
        json={"models": ["claude-sonnet-4-6", "gpt-5.5"]},
    )
    assert response.status_code == 200
    assert response.json()["retired_count"] == 0


def test_ensure_gemini_retired():
    data = client.get("/v1/ensure", params={"model": "gemini-2.0-flash"}).json()
    assert data["safe_model"] == "gemini-3.5-flash"
