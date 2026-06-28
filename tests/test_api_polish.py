"""API polish: headers, model detail, POST ensure."""

from __future__ import annotations

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_alive_response_headers():
    response = client.get("/v1/alive", params={"model": "claude-sonnet-4-20250514"})
    assert response.status_code == 410
    assert response.headers["X-Model-Status"] == "retired"
    assert response.headers["X-Replacement"] == "claude-sonnet-4-6"
    assert "ETag" in response.headers


def test_health_includes_etag_fields():
    data = client.get("/v1/health").json()
    assert "registry_etag" in data
    assert "alias_count" in data
    assert data["model_count"] >= 150


def test_get_model_detail():
    data = client.get("/v1/models/claude-sonnet-4-6").json()
    assert data["status"] == "active"
    assert data["entry"]["provider"] == "anthropic"


def test_get_model_unknown_404():
    response = client.get("/v1/models/totally-unknown-xyz-abc")
    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/problem+json")


def test_post_ensure():
    response = client.post(
        "/v1/ensure",
        json={"model": "claude-sonnet-4-20250514"},
    )
    assert response.status_code == 200
    assert response.json()["safe_model"] == "claude-sonnet-4-6"
    assert response.headers["X-Safe-Model"] == "claude-sonnet-4-6"


def test_resolve_includes_chain():
    data = client.get("/v1/resolve", params={"model": "gemini-2.0-flash"}).json()
    assert data["resolved"] == "gemini-3.5-flash"
    assert "chain" in data
