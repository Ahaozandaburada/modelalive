"""Registry graph validation."""

from __future__ import annotations

import json

import pytest

from modelalive.validate import validate_registry


def test_no_alias_cycles_in_production_registry():
    errors = [i for i in validate_registry() if i.level == "error"]
    assert not errors, errors


def test_detects_alias_cycle(tmp_path):
    registry = {
        "version": "2026-06-28",
        "schema_version": 2,
        "sources": {"openai": {"url": "https://example.com", "checked_at": "2026-06-28"}},
        "aliases": {"a": "b", "b": "c", "c": "a"},
        "models": {
            "a": {"provider": "openai", "status": "active", "source": "openai"},
            "b": {"provider": "openai", "status": "active", "source": "openai"},
            "c": {"provider": "openai", "status": "active", "source": "openai"},
        },
    }
    path = tmp_path / "models.json"
    path.write_text(json.dumps(registry), encoding="utf-8")
    issues = validate_registry(path)
    assert any("cycle" in issue.message.lower() for issue in issues)


def test_detects_replacement_cycle(tmp_path):
    registry = {
        "version": "2026-06-28",
        "schema_version": 2,
        "sources": {"openai": {"url": "https://example.com", "checked_at": "2026-06-28"}},
        "aliases": {},
        "models": {
            "m1": {
                "provider": "openai",
                "status": "retired",
                "retired_at": "2020-01-01",
                "replacement": "m2",
                "source": "openai",
            },
            "m2": {
                "provider": "openai",
                "status": "retired",
                "retired_at": "2020-01-01",
                "replacement": "m1",
                "source": "openai",
            },
        },
    }
    path = tmp_path / "models.json"
    path.write_text(json.dumps(registry), encoding="utf-8")
    issues = validate_registry(path)
    assert any("cycle" in issue.message.lower() for issue in issues)
