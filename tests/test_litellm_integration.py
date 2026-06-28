"""LiteLLM integration tests (no live LLM calls)."""

from __future__ import annotations

import modelalive
from modelalive.integrations.litellm import patch_litellm


def test_completion_ensure_without_litellm_call(monkeypatch):
    """patch_litellm wraps litellm if installed."""
    calls: list[str] = []

    class FakeLiteLLM:
        @staticmethod
        def completion(model, messages, **kwargs):
            calls.append(model)
            return {"model": model}

    import sys

    fake = FakeLiteLLM()
    monkeypatch.setitem(sys.modules, "litellm", fake)
    patch_litellm()

    fake.completion("claude-sonnet-4-20250514", [])
    assert calls[0] == "claude-sonnet-4-6"


def test_integrations_export():
    from modelalive.integrations import completion, patch_litellm

    assert callable(completion)
    assert callable(patch_litellm)

    assert modelalive.ensure("qwen-max") == "qwen3.7-max"
