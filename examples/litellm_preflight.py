"""LiteLLM: wrap completion() with modelalive.ensure()."""

from __future__ import annotations

import modelalive


def litellm_completion(model: str, messages: list[dict], **kwargs):
    import litellm

    safe = modelalive.ensure(model)
    if safe != model:
        print(f"[modelalive] {model!r} → {safe!r}")
    return litellm.completion(model=safe, messages=messages, **kwargs)


if __name__ == "__main__":
    print("safe:", modelalive.ensure("claude-sonnet-4-20250514"))
