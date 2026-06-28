"""Bedrock and Azure host-specific registry coverage."""

from __future__ import annotations

import modelalive


def test_bedrock_host_provider():
    result = modelalive.alive("anthropic.claude-sonnet-4-6-v1:0")
    assert result.provider == "bedrock"
    assert result.status == "active"


def test_bedrock_retired_inherits_lifecycle():
    result = modelalive.alive("anthropic.claude-sonnet-4-20250514-v1:0")
    assert result.provider == "bedrock"
    assert result.status == "retired"
    assert result.replacement == "anthropic.claude-sonnet-4-6-v1:0"


def test_bedrock_regional_alias():
    result = modelalive.alive("us.anthropic.claude-sonnet-4-6-v1:0")
    assert result.provider == "bedrock"
    assert modelalive.ensure("us.anthropic.claude-sonnet-4-6-v1:0") == "anthropic.claude-sonnet-4-6-v1:0"


def test_azure_host_provider():
    result = modelalive.alive("azure/gpt-4o")
    assert result.provider == "azure"
    assert result.status == "active"


def test_azure_claude_crosswalk():
    result = modelalive.alive("azure/claude-sonnet-4-6")
    assert result.provider == "azure"
    assert modelalive.ensure("azure/claude-sonnet-4-6") == "azure/claude-sonnet-4-6"
