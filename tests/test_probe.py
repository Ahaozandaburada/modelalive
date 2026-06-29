"""Probe backend resolution tests."""

from __future__ import annotations

import pytest

from modelalive.probe import resolve_probe_backend


def test_resolve_anthropic_from_model_id():
    assert resolve_probe_backend("claude-sonnet-4-6") == "anthropic"


def test_resolve_google_from_model_id():
    assert resolve_probe_backend("gemini-3.5-flash") == "google"


def test_resolve_openai_default():
    assert resolve_probe_backend("gpt-4o") == "openai"


def test_resolve_forced_provider():
    assert resolve_probe_backend("claude-sonnet-4-6", provider="openai") == "openai"


def test_probe_config_errors_without_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("MODELALIVE_PROBE_API_KEY", raising=False)
    from modelalive.probe import probe_config

    with pytest.raises(RuntimeError):
        probe_config("openai", "gpt-4o")
