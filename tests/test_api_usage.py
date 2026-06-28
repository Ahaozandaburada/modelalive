"""Usage metering and quota tests."""

from __future__ import annotations

import importlib

from fastapi.testclient import TestClient


def test_usage_headers_on_alive():
    import api.main as main_module

    client = TestClient(main_module.app)
    response = client.get("/v1/alive", params={"model": "gpt-4o"})
    assert response.status_code == 200
    assert "X-Usage-Count" in response.headers
    assert "X-Usage-Limit" in response.headers
    assert response.headers["X-Usage-Tier"] == "free"


def test_usage_endpoint():
    import api.main as main_module

    client = TestClient(main_module.app)
    client.get("/v1/alive", params={"model": "gpt-4o"})
    data = client.get("/v1/usage").json()
    assert data["checks_used"] >= 1
    assert data["tier"] == "free"
    assert data["checks_limit"] == 100


def test_quota_enforcement(monkeypatch):
    monkeypatch.setenv("MODELALIVE_ENFORCE_QUOTA", "1")
    import api.main as main_module
    import api.usage as usage_module

    importlib.reload(usage_module)
    importlib.reload(main_module)
    usage_module.get_tracker().counts.clear()

    client = TestClient(main_module.app)
    assert client.get("/v1/alive", params={"model": "gpt-4o"}).status_code == 200

    # Exhaust free tier (100 checks) — patch limit for speed
    usage_module.TIERS["free"]["monthly_checks"] = 1
    usage_module.get_tracker().counts.clear()
    client2 = TestClient(main_module.app)
    assert client2.get("/v1/alive", params={"model": "gpt-4o"}).status_code == 200
    blocked = client2.get("/v1/alive", params={"model": "gpt-4o"})
    assert blocked.status_code == 402

    monkeypatch.delenv("MODELALIVE_ENFORCE_QUOTA", raising=False)
    usage_module.TIERS["free"]["monthly_checks"] = 100
    importlib.reload(usage_module)
    importlib.reload(main_module)
