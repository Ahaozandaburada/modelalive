"""Usage metering and quota tests."""

from __future__ import annotations

import importlib

import pytest
from fastapi.testclient import TestClient

from api.store import reset_store


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("MODELALIVE_DB_PATH", str(tmp_path / "usage.db"))
    monkeypatch.delenv("MODELALIVE_ENFORCE_QUOTA", raising=False)
    reset_store(tmp_path / "usage.db")
    import api.main as main_module

    importlib.reload(main_module)
    return TestClient(main_module.app)


def test_usage_headers_on_alive(client):
    response = client.get("/v1/alive", params={"model": "gpt-4o"})
    assert response.status_code == 200
    assert "X-Usage-Count" in response.headers
    assert response.headers["X-Usage-Tier"] == "free"


def test_usage_endpoint(client):
    client.get("/v1/alive", params={"model": "gpt-4o"})
    data = client.get("/v1/usage").json()
    assert data["checks_used"] >= 1
    assert data["tier"] == "free"
    assert data["checks_limit"] == 100


def test_quota_enforcement(monkeypatch, tmp_path):
    monkeypatch.setenv("MODELALIVE_DB_PATH", str(tmp_path / "quota.db"))
    monkeypatch.setenv("MODELALIVE_ENFORCE_QUOTA", "1")
    reset_store(tmp_path / "quota.db")
    import api.usage as usage_module
    import api.main as main_module

    usage_module.reset_ip_tracker()
    usage_module.TIERS["free"]["monthly_checks"] = 1
    importlib.reload(main_module)
    client = TestClient(main_module.app)
    assert client.get("/v1/alive", params={"model": "gpt-4o"}).status_code == 200
    blocked = client.get("/v1/alive", params={"model": "gpt-4o"})
    assert blocked.status_code == 402

    monkeypatch.delenv("MODELALIVE_ENFORCE_QUOTA", raising=False)
    usage_module.TIERS["free"]["monthly_checks"] = 100
