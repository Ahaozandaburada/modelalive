from __future__ import annotations

import re

_MODEL_ID_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._:/-]{0,200}$")
_FINE_TUNED_PREFIX = re.compile(r"^ft:([^:]+(?::[^:]+)*)")


def normalize_model(model: str) -> str:
    """Normalize a model ID for lookup."""
    cleaned = model.strip()
    if not cleaned:
        raise ValueError("Model ID cannot be empty")

    # OpenAI fine-tuned: ft:gpt-4o-mini:org:name:id → base model for lookup
    ft_match = _FINE_TUNED_PREFIX.match(cleaned)
    if ft_match:
        base = ft_match.group(1).split(":")[0]
        if base:
            cleaned = base

    if not _MODEL_ID_PATTERN.match(cleaned):
        raise ValueError(f"Invalid model ID format: {model!r}")
    return cleaned
