from datetime import date

import pytest
from fastapi.testclient import TestClient

from modelalive import alive, assert_registry_valid, check, ensure, resolve, validate_registry
from modelalive.exceptions import ModelRetiredError, ModelUnknownError
from modelalive.normalize import normalize_model
from modelalive.lifecycle import effective_status
from api.main import app


def test_registry_is_valid():
    assert_registry_valid()
    issues = validate_registry()
    errors = [issue for issue in issues if issue.level == "error"]
    assert not errors


def test_retired_model_not_alive():
    result = alive("claude-sonnet-4-20250514")
    assert result.alive is False
    assert result.status == "retired"
    assert result.replacement == "claude-sonnet-4-6"
    assert result.confidence == "verified"
    assert result.source_url is not None


def test_check_raises_on_retired():
    with pytest.raises(ModelRetiredError) as exc:
        check("claude-sonnet-4-20250514")
    assert exc.value.result.replacement == "claude-sonnet-4-6"


def test_strict_unknown_raises():
    with pytest.raises(ModelUnknownError):
        check("totally-unknown-model-xyz", strict_unknown=True)


def test_active_model_alive():
    result = alive("claude-sonnet-4-6")
    assert result.alive is True
    assert result.status == "active"


def test_unknown_model_assumed_alive():
    result = alive("some-future-model-xyz")
    assert result.alive is True
    assert result.status == "unknown"
    assert result.confidence == "unknown"


def test_resolve_returns_active_replacement():
    assert resolve("claude-sonnet-4-20250514") == "claude-sonnet-4-6"
    assert resolve("claude-sonnet-4-6") == "claude-sonnet-4-6"
    assert resolve("gemini-2.0-flash") == "gemini-3.5-flash"


def test_ensure_returns_safe_model():
    assert ensure("claude-sonnet-4-20250514") == "claude-sonnet-4-6"
    assert ensure("claude-sonnet-4-6") == "claude-sonnet-4-6"


def test_ensure_auto_replaces_retired():
    assert ensure("claude-sonnet-4-20250514") == "claude-sonnet-4-6"


def test_ensure_strict_unknown():
    with pytest.raises(ModelUnknownError):
        ensure("totally-unknown-model-xyz", strict_unknown=True)


def test_deprecated_mythos_still_alive():
    result = alive("claude-mythos-preview", today=date(2026, 6, 28))
    assert result.alive is True
    assert result.status == "deprecated"
    assert result.days_until_retirement == 2


def test_alias_resolves_to_retired_model():
    result = alive("claude-3-5-sonnet-latest")
    assert result.aliased is True
    assert result.canonical_model == "claude-3-5-sonnet-20241022"
    assert result.status == "retired"


def test_effective_status_from_past_retired_at():
    entry = {"status": "deprecated", "retired_at": "2026-06-15"}
    assert effective_status(entry, today=date(2026, 6, 28)) == "retired"


def test_gemini_2_flash_retired():
    result = alive("gemini-2.0-flash", today=date(2026, 6, 28))
    assert result.alive is False
    assert result.status == "retired"
    assert result.replacement == "gemini-3.5-flash"
    assert result.provider == "google"


def test_gemini_alias():
    result = alive("gemini-2.0-flash-latest", today=date(2026, 6, 28))
    assert result.aliased is True
    assert result.status == "retired"


def test_openai_upcoming_deprecation():
    result = alive("gpt-5-2025-08-07", today=date(2026, 6, 28))
    assert result.status == "deprecated"
    assert result.replacement == "gpt-5.5"
    assert result.days_until_retirement == 166


def test_normalize_rejects_empty():
    with pytest.raises(ValueError):
        normalize_model("   ")


def test_replacement_chains_end_active():
    issues = validate_registry()
    chain_errors = [
        issue
        for issue in issues
        if issue.level == "error" and "replacement chain" in issue.message
    ]
    assert not chain_errors


class TestAPI:
    client = TestClient(app)

    def test_health(self):
        response = self.client.get("/v1/health")
        assert response.status_code == 200
        assert response.json()["model_count"] >= 60

    def test_alive_retired_410(self):
        response = self.client.get("/v1/alive", params={"model": "claude-sonnet-4-20250514"})
        assert response.status_code == 410
        assert response.json()["replacement"] == "claude-sonnet-4-6"

    def test_batch_alive(self):
        response = self.client.post(
            "/v1/alive/batch",
            json={"models": ["claude-sonnet-4-6", "claude-sonnet-4-20250514"]},
        )
        assert response.status_code == 410
        body = response.json()
        assert body["retired_count"] == 1

    def test_validate_endpoint(self):
        response = self.client.get("/v1/validate")
        assert response.status_code == 200
        assert response.json()["valid"] is True

    def test_ensure_endpoint(self):
        response = self.client.get("/v1/ensure", params={"model": "claude-sonnet-4-20250514"})
        assert response.status_code == 200
        assert response.json()["safe_model"] == "claude-sonnet-4-6"

    def test_ensure_retired_direct(self):
        response = self.client.get(
            "/v1/ensure",
            params={"model": "claude-sonnet-4-20250514", "strict_unknown": "true"},
        )
        assert response.status_code == 200
        assert response.json()["safe_model"] == "claude-sonnet-4-6"
