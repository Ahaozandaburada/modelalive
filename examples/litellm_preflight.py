"""LiteLLM: wrap completion() with modelalive.ensure()."""

from __future__ import annotations

import modelalive
from modelalive.integrations.litellm import completion, patch_litellm

if __name__ == "__main__":
    patch_litellm()
    print("safe:", modelalive.ensure("claude-sonnet-4-20250514"))
    print("patched litellm.completion — call litellm.completion(...) as usual")
