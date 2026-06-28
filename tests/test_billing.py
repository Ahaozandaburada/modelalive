"""Billing store and API tests."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from api.store import BillingStore, generate_api_key, reset_store


@pytest.fixture
def store(tmp_path, monkeypatch):
    db = tmp_path / "test.db"
    monkeypatch.setenv("MODELALIVE_DB_PATH", str(db))
    return reset_store(db)


def test_generate_and_lookup_key(store):
    raw = generate_api_key()
    assert raw.startswith("ma_live_")
    store.create_key(raw_key=raw, tier="pro", email="a@b.com")
    record = store.lookup_key(raw)
    assert record is not None
    assert record["tier"] == "pro"
    assert record["email"] == "a@b.com"


def test_usage_increment_and_month_reset(store):
    raw = generate_api_key()
    store.create_key(raw_key=raw, tier="pro")
    assert store.get_usage(raw) == (0, "pro")
    assert store.increment_usage(raw) == 1
    assert store.get_usage(raw) == (1, "pro")


def test_session_key_one_time_retrieval(store):
    raw = generate_api_key()
    store.create_key(raw_key=raw, tier="pro", checkout_session_id="cs_test_123")
    store.store_session_key("cs_test_123", raw)
    assert store.pop_session_key("cs_test_123") == raw
    assert store.pop_session_key("cs_test_123") is None


def test_billing_plans_endpoint(store, monkeypatch):
    monkeypatch.setenv("MODELALIVE_DB_PATH", str(store.path))
    import importlib

    import api.main as main_module

    importlib.reload(main_module)
    client = TestClient(main_module.app)
    data = client.get("/v1/billing/plans").json()
    assert "free" in data["plans"]
    assert "pro" in data["plans"]
    assert data["plans"]["pro"]["monthly_checks"] == 100_000


def test_pro_key_gets_pro_tier_on_usage(store, monkeypatch):
    monkeypatch.setenv("MODELALIVE_DB_PATH", str(store.path))
    raw = generate_api_key()
    store.create_key(raw_key=raw, tier="pro")
    import importlib

    import api.main as main_module

    importlib.reload(main_module)
    client = TestClient(main_module.app)
    response = client.get("/v1/alive", params={"model": "gpt-4o"}, headers={"X-API-Key": raw})
    assert response.status_code == 200
    assert response.headers["X-Usage-Tier"] == "pro"
    assert response.headers["X-Usage-Limit"] == "100000"
