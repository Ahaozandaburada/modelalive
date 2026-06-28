"""Public status page."""

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_status_json():
    data = client.get("/v1/status").json()
    assert data["service"] == "Model Alive API"
    assert data["model_count"] >= 500
    assert data["status"] in {"operational", "degraded"}


def test_status_html():
    response = client.get("/status")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Model Alive" in response.text
