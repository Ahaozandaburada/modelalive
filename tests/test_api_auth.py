"""API key authentication tests."""

from __future__ import annotations

import importlib

import pytest
from fastapi.testclient import TestClient

from api.store import generate_api_key, reset_store


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("MODELALIVE_DB_PATH", str(tmp_path / "auth.db"))
    monkeypatch.delenv("MODELALIVE_REQUIRE_API_KEY", raising=False)
    reset_store(tmp_path / "auth.db")
    import api.main as main_module

    importlib.reload(main_module)
    return TestClient(main_module.app)


def test_request_id_header(client):
    response = client.get("/v1/health")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers


def test_valid_store_key_authenticates(client, tmp_path):
    raw = generate_api_key()
    reset_store(tmp_path / "auth.db").create_key(raw_key=raw, tier="pro")
    response = client.get("/v1/alive", params={"model": "gpt-4o"}, headers={"X-API-Key": raw})
    assert response.status_code == 200
    assert response.headers.get("X-Authenticated") == "true"


def test_api_key_required_when_enforced(client, monkeypatch):
    monkeypatch.setenv("MODELALIVE_REQUIRE_API_KEY", "1")
    import api.main as main_module

    importlib.reload(main_module)
    limited = TestClient(main_module.app)
    denied = limited.get("/v1/alive", params={"model": "gpt-4o"})
    assert denied.status_code == 401

    monkeypatch.delenv("MODELALIVE_REQUIRE_API_KEY", raising=False)
    importlib.reload(main_module)
