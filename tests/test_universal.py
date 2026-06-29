"""Universal resolution across inference surfaces."""

from __future__ import annotations

import pytest

from modelalive import alive
from modelalive.normalize import normalize_model
from modelalive.universal import universal_resolve


def test_openrouter_prefix_strips():
    assert normalize_model("openrouter/anthropic/claude-sonnet-4-6") == "anthropic/claude-sonnet-4-6"


def test_ollama_prefix_and_latest_tag():
    assert normalize_model("ollama/llama3.2:latest") == "llama3.2"


def test_huggingface_prefix():
    assert normalize_model("huggingface/meta-llama/llama-3.3-70b-instruct") == "meta-llama/llama-3.3-70b-instruct"


def test_openrouter_slug_resolves_to_canonical():
    resolved = universal_resolve("anthropic/claude-sonnet-4-6")
    assert resolved.in_registry
    assert resolved.resolved == "claude-sonnet-4-6"


def test_openrouter_prefixed_slug():
    resolved = universal_resolve("openrouter/openai/gpt-4o")
    assert resolved.in_registry
    assert resolved.resolved == "gpt-4o"


def test_ollama_latest_alias_chain():
    result = alive("llama3.2:latest")
    assert result.status == "active"
    assert result.canonical_model == "meta-llama/Llama-3.2-3B-Instruct"


def test_bedrock_cross_region_prefix():
    assert normalize_model("us.anthropic.claude-sonnet-4-6-v1:0") == "anthropic.claude-sonnet-4-6-v1:0"


def test_case_insensitive_hf_alias():
    resolved = universal_resolve("meta-llama/llama-3.3-70b-instruct")
    assert resolved.in_registry
    assert "Llama-3.3-70B" in resolved.resolved or resolved.resolved == "meta-llama/Llama-3.3-70B-Instruct"
