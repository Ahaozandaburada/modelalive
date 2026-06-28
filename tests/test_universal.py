"""Universal multi-provider registry tests."""

from __future__ import annotations

import modelalive
from modelalive.providers import list_provider_keys, provider_label


def test_provider_count():
    keys = list_provider_keys()
    assert len(keys) >= 15
    assert "xai" in keys
    assert "together" in keys
    assert "fireworks" in keys
    assert "openrouter" in keys


def test_openrouter_alias_to_openai():
    result = modelalive.alive("openai/gpt-4o")
    assert result.status == "active"
    assert result.canonical_model == "gpt-4o"


def test_openrouter_anthropic_alias():
    result = modelalive.alive("anthropic/claude-sonnet-4-6")
    assert result.status == "active"


def test_xai_grok3_retired():
    result = modelalive.alive("grok-3")
    assert result.status == "retired"
    assert modelalive.ensure("grok-3") == "grok-4.3"


def test_together_host_specific_model():
    result = modelalive.alive("meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo")
    assert result.provider == "together"
    assert result.status == "retired"


def test_fireworks_host_model():
    result = modelalive.alive("fireworks/kimi-k2p5")
    assert result.status == "retired"
    assert modelalive.resolve("fireworks/kimi-k2p5") == "fireworks/kimi-k2p6"


def test_perplexity_sonar_active():
    assert modelalive.alive("sonar").status == "active"


def test_provider_labels():
    assert provider_label("xai") == "xAI (Grok)"
    assert provider_label("together") == "Together AI"
