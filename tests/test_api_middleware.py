"""API middleware: request ID and rate limiting."""

from __future__ import annotations

import os

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_request_id_header():
    response = client.get("/v1/health")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert len(response.headers["X-Request-ID"]) >= 8


def test_request_id_passthrough():
    response = client.get("/v1/health", headers={"X-Request-ID": "test-req-123"})
    assert response.headers["X-Request-ID"] == "test-req-123"


def test_rate_limit(monkeypatch):
    monkeypatch.setenv("MODELALIVE_RATE_LIMIT", "1")
    import importlib

    import api.main as main_module

    importlib.reload(main_module)
    limited = TestClient(main_module.app)

    assert limited.get("/v1/alive", params={"model": "gpt-4o"}).status_code == 200
    blocked = limited.get("/v1/alive", params={"model": "gpt-4o"})
    assert blocked.status_code == 429
    assert blocked.headers["content-type"].startswith("application/problem+json")

    monkeypatch.delenv("MODELALIVE_RATE_LIMIT", raising=False)
    importlib.reload(main_module)
