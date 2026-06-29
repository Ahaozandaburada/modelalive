from __future__ import annotations

import re

_MODEL_ID_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._:/@-]{0,200}$")
_FINE_TUNED_PREFIX = re.compile(r"^ft:([^:]+(?::[^:]+)*)")
_STRIP_PREFIXES = (
    "openrouter/",
    "ollama/",
    "huggingface/",
    "hf/",
    "models/",
    "litellm/",
    "vertex/",
)
_OLLAMA_TAG = re.compile(
    r"^([a-zA-Z0-9][a-zA-Z0-9._-]{0,120}):(latest|main|\d+b|\d+\.\d+b)$",
    re.IGNORECASE,
)


def normalize_model(model: str) -> str:
    """Normalize any LLM model ID from major APIs, hosts, and local runtimes."""
    cleaned = model.strip()
    if not cleaned:
        raise ValueError("Model ID cannot be empty")

    # OpenAI fine-tuned: ft:gpt-4o-mini:org:name:id → base model
    ft_match = _FINE_TUNED_PREFIX.match(cleaned)
    if ft_match:
        base = ft_match.group(1).split(":")[0]
        if base:
            cleaned = base

    lowered = cleaned.lower()
    for prefix in _STRIP_PREFIXES:
        if lowered.startswith(prefix):
            cleaned = cleaned[len(prefix) :]
            lowered = cleaned.lower()
            break

    # Ollama tags: llama3.2:latest → llama3.2
    ollama_match = _OLLAMA_TAG.match(cleaned)
    if ollama_match:
        cleaned = ollama_match.group(1)

    # Bedrock cross-region prefix: us.anthropic.claude-… → anthropic.claude-…
    if cleaned.startswith(("us.", "eu.", "apac.", "global.")):
        parts = cleaned.split(".", 1)
        if len(parts) == 2 and parts[1].startswith(("anthropic.", "amazon.", "meta.", "ai21.")):
            cleaned = parts[1]

    if not _MODEL_ID_PATTERN.match(cleaned):
        raise ValueError(f"Invalid model ID format: {model!r}")
    return cleaned
