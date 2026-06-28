from __future__ import annotations

import re

_MODEL_ID_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,127}$")


def normalize_model(model: str) -> str:
    """Normalize a model ID for lookup."""
    cleaned = model.strip()
    if not cleaned:
        raise ValueError("Model ID cannot be empty")
    if not _MODEL_ID_PATTERN.match(cleaned):
        raise ValueError(f"Invalid model ID format: {model!r}")
    return cleaned
