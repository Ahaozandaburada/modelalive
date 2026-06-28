"""API key authentication tests."""

from __future__ import annotations

import importlib

from fastapi.testclient import TestClient


def test_api_key_required(monkeypatch):
    monkeypatch.setenv("MODELALIVE_REQUIRE_API_KEY", "1")
    monkeypatch.setenv("MODELALIVE_API_KEYS", "test-key-123")
    import api.main as main_module

    importlib.reload(main_module)
    client = TestClient(main_module.app)

    denied = client.get("/v1/alive", params={"model": "gpt-4o"})
    assert denied.status_code == 401

    ok = client.get("/v1/alive", params={"model": "gpt-4o"}, headers={"X-API-Key": "test-key-123"})
    assert ok.status_code == 200
    assert ok.headers.get("X-Authenticated") == "true"

    health = client.get("/v1/health")
    assert health.status_code == 200

    monkeypatch.delenv("MODELALIVE_REQUIRE_API_KEY", raising=False)
    monkeypatch.delenv("MODELALIVE_API_KEYS", raising=False)
    importlib.reload(main_module)
