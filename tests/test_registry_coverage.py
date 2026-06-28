"""Extended test suite — registry coverage and edge cases."""

from __future__ import annotations

from datetime import date

import pytest

from modelalive import alive, ensure, resolve
from modelalive.config_file import load_config
from modelalive.lifecycle import effective_status, parse_date
from modelalive.registry import load_registry, resolve_alias
from modelalive.settings import default_strict_unknown, env_flag
from modelalive.validate import validate_registry


@pytest.fixture
def registry():
    return load_registry()


def test_registry_has_minimum_model_count(registry):
    assert len(registry["models"]) >= 200


def test_all_sources_have_urls(registry):
    for key, meta in registry["sources"].items():
        assert meta.get("url"), f"source {key} missing url"
        assert meta.get("checked_at"), f"source {key} missing checked_at"


@pytest.mark.parametrize(
    "model,replacement",
    [
        ("claude-sonnet-4-20250514", "claude-sonnet-4-6"),
        ("claude-opus-4-20250514", "claude-opus-4-8"),
        ("gemini-2.0-flash", "gemini-3.5-flash"),
        ("gpt-4-0314", "gpt-4o"),
        ("llama3-70b-8192", "llama-3.3-70b-versatile"),
    ],
)
def test_retired_models_resolve(model, replacement):
    result = alive(model)
    assert result.status == "retired"
    assert not result.alive
    assert resolve(model) == replacement
    assert ensure(model) == replacement


@pytest.mark.parametrize(
    "model",
    [
        "claude-sonnet-4-6",
        "claude-opus-4-8",
        "gpt-5.5",
        "gpt-4o",
        "gemini-3.5-flash",
    ],
)
def test_active_models(model):
    result = alive(model)
    assert result.status == "active"
    assert result.alive


def test_groq_source_in_registry(registry):
    assert "groq" in registry["sources"]


def test_alias_claude_sonnet_latest():
    result = alive("claude-3-5-sonnet-latest")
    assert result.aliased
    assert result.status == "retired"


def test_alias_cycle_detection(tmp_path):
    import json

    reg = {
        "version": "2026-01-01",
        "schema_version": 2,
        "sources": {},
        "aliases": {"model-a": "model-b", "model-b": "model-a"},
        "models": {},
    }
    path = tmp_path / "registry.json"
    path.write_text(json.dumps(reg), encoding="utf-8")
    with pytest.raises(ValueError, match="cycle"):
        resolve_alias("model-a", registry_path=path)


def test_parse_date_valid():
    assert parse_date("2026-06-15") == date(2026, 6, 15)


def test_parse_date_none():
    assert parse_date(None) is None


def test_effective_status_legacy():
    assert effective_status({"status": "legacy", "retired_at": "2099-01-01"}) == "deprecated"


def test_validate_no_errors():
    errors = [i for i in validate_registry() if i.level == "error"]
    assert not errors


def test_load_config_defaults(tmp_path):
    cfg = load_config(tmp_path / "missing.toml")
    assert cfg.models == []


def test_load_config_from_file(tmp_path):
    path = tmp_path / "modelalive.toml"
    path.write_text('models = ["claude-sonnet-4-6"]\n', encoding="utf-8")
    cfg = load_config(path)
    assert cfg.models == ["claude-sonnet-4-6"]


def test_env_flag(monkeypatch):
    monkeypatch.setenv("MODELALIVE_STRICT", "1")
    assert env_flag("MODELALIVE_STRICT") is True
    assert default_strict_unknown() is True


def test_breaking_changes_on_opus_48():
    result = alive("claude-opus-4-8")
    assert result.breaking_changes


def test_migrate_url_present(registry):
    for model_id, entry in registry["models"].items():
        if entry.get("source"):
            assert entry.get("migrate_url"), f"{model_id} missing migrate_url"


def test_deprecated_has_retired_at(registry):
    for model_id, entry in registry["models"].items():
        if entry.get("status") == "deprecated":
            assert entry.get("retired_at"), f"{model_id} deprecated without retired_at"


def test_replacement_chain_ends_active(registry):
    errors = [
        i
        for i in validate_registry()
        if i.level == "error" and "replacement chain" in i.message
    ]
    assert not errors
