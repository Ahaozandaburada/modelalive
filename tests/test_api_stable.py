"""API routes for behavioral stability."""

from __future__ import annotations

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_stable_prompts():
    data = client.get("/v1/stable/prompts").json()
    assert data["count"] >= 5
    assert data["prompts"][0]["id"]


def test_stable_fingerprint_build():
    body = {
        "model": "gpt-4o",
        "responses": {
            "json_echo": ['{"ok": true, "n": 42}'],
            "math_fixed": ["391"],
            "refusal_probe": ["no"],
            "code_snippet": ["def f(): pass"],
            "style_haiku": ["a\nb\nc"],
        },
    }
    data = client.post("/v1/stable/fingerprint", json=body).json()
    assert data["kind"] == "modelalive-stable-fingerprint"
    assert data["model"] == "gpt-4o"
    assert len(data["prompts"]) == 5


def test_stable_compare_stable():
    responses = {
        "json_echo": ['{"ok": true, "n": 42}'],
        "math_fixed": ["391"],
        "refusal_probe": ["no"],
        "code_snippet": ["def f(): pass"],
        "style_haiku": ["a\nb\nc"],
    }
    fp = client.post(
        "/v1/stable/fingerprint",
        json={"model": "gpt-4o", "responses": responses},
    ).json()
    response = client.post("/v1/stable/compare", json={"baseline": fp, "current": fp})
    assert response.status_code == 200
    assert response.headers["X-Stable"] == "true"
    assert response.json()["stable"] is True


def test_stable_compare_drift():
    base = {
        "json_echo": ['{"ok": true, "n": 42}'],
        "math_fixed": ["391"],
        "refusal_probe": ["no"],
        "code_snippet": ["def f(): pass"],
        "style_haiku": ["a\nb\nc"],
    }
    shifted = dict(base)
    shifted["math_fixed"] = ["999"]
    shifted["code_snippet"] = ["def add(a,b): return a+b"]
    shifted["style_haiku"] = ["totally different poem here now"]
    b = client.post("/v1/stable/fingerprint", json={"model": "gpt-4o", "responses": base}).json()
    c = client.post("/v1/stable/fingerprint", json={"model": "gpt-4o", "responses": shifted}).json()
    response = client.post("/v1/stable/compare", json={"baseline": b, "current": c, "threshold": 0.25})
    assert response.status_code == 409
    assert response.headers["X-Stable"] == "false"
    assert response.json()["stable"] is False
