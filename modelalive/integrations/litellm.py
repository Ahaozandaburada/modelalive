"""LiteLLM integration — pre-flight gate before every completion."""

from __future__ import annotations

from typing import Any

import modelalive


class ModelAliveLiteLLMCallback:
    """LiteLLM custom callback that runs modelalive.ensure() before LLM calls."""

    def log_pre_api_call(self, model: str, messages: list, kwargs: dict) -> tuple[str, list, dict]:
        safe = modelalive.ensure(model)
        if safe != model:
            kwargs = dict(kwargs)
            kwargs.setdefault("metadata", {})["modelalive_original"] = model
            return safe, messages, kwargs
        return model, messages, kwargs


def patch_litellm() -> None:
    """Monkey-patch litellm.completion to auto-ensure models."""
    import litellm

    if getattr(litellm.completion, "_modelalive_patched", False):
        return

    original = litellm.completion

    def wrapped(model: str, *args: Any, **kwargs: Any):
        safe = modelalive.ensure(model)
        if safe != model:
            kwargs.setdefault("metadata", {})["modelalive_original"] = model
        return original(safe, *args, **kwargs)

    wrapped._modelalive_patched = True  # type: ignore[attr-defined]
    litellm.completion = wrapped


def completion(model: str, messages: list[dict], **kwargs: Any):
    """Drop-in litellm.completion with modelalive pre-flight."""
    import litellm

    safe = modelalive.ensure(model)
    if safe != model:
        kwargs.setdefault("metadata", {})["modelalive_original"] = model
    return litellm.completion(model=safe, messages=messages, **kwargs)
