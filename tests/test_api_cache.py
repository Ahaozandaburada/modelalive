"""HTTP caching: ETag + If-None-Match."""

from __future__ import annotations

from fastapi.testclient import TestClient

from api.main import app
from modelalive.registry import registry_hash

client = TestClient(app)
ETAG = f'"{registry_hash()}"'


def test_health_returns_etag():
    response = client.get("/v1/health")
    assert response.status_code == 200
    assert response.headers.get("ETag") == ETAG


def test_if_none_match_returns_304():
    first = client.get("/v1/health")
    etag = first.headers["ETag"]
    cached = client.get("/v1/health", headers={"If-None-Match": etag})
    assert cached.status_code == 304
    assert cached.headers.get("ETag") == etag
    assert cached.content == b""


def test_registry_list_cached():
    response = client.get("/v1/registry", headers={"If-None-Match": ETAG})
    assert response.status_code == 304


def test_alive_cached_with_etag():
    etag = client.get("/v1/alive", params={"model": "gpt-4o"}).headers["ETag"]
    cached = client.get(
        "/v1/alive",
        params={"model": "gpt-4o"},
        headers={"If-None-Match": etag},
    )
    assert cached.status_code == 304


def test_sources_cached():
    response = client.get("/v1/sources", headers={"If-None-Match": ETAG})
    assert response.status_code == 304
