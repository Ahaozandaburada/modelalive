"""Normalization and alias edge cases."""

from __future__ import annotations

import pytest

from modelalive import alive, resolve, resolve_detail
from modelalive.normalize import normalize_model


def test_fine_tuned_prefix_normalizes_to_base():
    assert normalize_model("ft:gpt-4o-mini:org-abc:my-model:abc123") == "gpt-4o-mini"


def test_fine_tuned_alive_uses_base():
    result = alive("ft:gpt-4o-mini:org:foo:bar")
    assert result.model == "gpt-4o-mini"
    assert result.status == "active"


def test_bedrock_alias_resolves():
    result = alive("anthropic.claude-sonnet-4-6-v1:0")
    assert result.status == "active"
    assert result.provider == "bedrock"
    assert result.canonical_model == "anthropic.claude-sonnet-4-6-v1:0"


def test_bedrock_retired_alias():
    result = alive("anthropic.claude-sonnet-4-20250514-v1:0")
    assert result.status == "retired"
    assert resolve("anthropic.claude-sonnet-4-20250514-v1:0") == "anthropic.claude-sonnet-4-6-v1:0"


def test_mistral_retired():
    result = alive("mistral-medium-2312")
    assert result.status == "retired"
    assert result.replacement == "mistral-large-2411"


def test_resolve_detail_merges_breaking_changes():
    detail = resolve_detail("claude-opus-4-20250514")
    assert detail["resolved"] == "claude-opus-4-8"
    assert isinstance(detail["breaking_changes"], list)
    assert len(detail["breaking_changes"]) >= 1


@pytest.mark.parametrize(
    "bad",
    ["", "   ", "model with spaces", "a" * 300],
)
def test_normalize_rejects_invalid(bad):
    with pytest.raises(ValueError):
        normalize_model(bad)
