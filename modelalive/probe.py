"""Live endpoint probe — Anthropic, Google Gemini, OpenAI-compatible."""

from __future__ import annotations

import os
from typing import Any, Literal

from modelalive.stable import list_stable_prompts

ProbeBackend = Literal["anthropic", "google", "openai"]


def resolve_probe_backend(model: str, provider: str | None = None) -> ProbeBackend:
    if provider:
        normalized = provider.strip().lower()
        if normalized in {"anthropic", "google", "openai"}:
            return normalized  # type: ignore[return-value]
        raise ValueError(f"Unknown probe provider: {provider}")

    forced = os.environ.get("MODELALIVE_PROBE_PROVIDER", "").strip().lower()
    if forced in {"anthropic", "google", "openai"}:
        return forced  # type: ignore[return-value]

    try:
        from modelalive.check import alive

        entry = alive(model)
        if entry.provider == "anthropic":
            return "anthropic"
        if entry.provider == "google":
            return "google"
    except Exception:
        pass

    lowered = model.lower()
    if lowered.startswith("claude") or lowered.startswith("anthropic."):
        return "anthropic"
    if lowered.startswith("gemini") or lowered.startswith("google/"):
        return "google"
    return "openai"


def probe_config(backend: ProbeBackend | None = None, model: str = "") -> tuple[str, str, ProbeBackend]:
    resolved = backend or resolve_probe_backend(model)

    if resolved == "anthropic":
        base = (
            os.environ.get("MODELALIVE_PROBE_BASE_URL", "").strip()
            or os.environ.get("ANTHROPIC_BASE_URL", "").strip()
            or "https://api.anthropic.com/v1"
        ).rstrip("/")
        key = (
            os.environ.get("MODELALIVE_PROBE_API_KEY", "").strip()
            or os.environ.get("ANTHROPIC_API_KEY", "").strip()
        )
        if not key:
            raise RuntimeError(
                "Set MODELALIVE_PROBE_API_KEY or ANTHROPIC_API_KEY to probe Anthropic."
            )
        return base, key, resolved

    if resolved == "google":
        base = (
            os.environ.get("MODELALIVE_PROBE_BASE_URL", "").strip()
            or os.environ.get("GOOGLE_API_BASE", "").strip()
            or "https://generativelanguage.googleapis.com/v1beta"
        ).rstrip("/")
        key = (
            os.environ.get("MODELALIVE_PROBE_API_KEY", "").strip()
            or os.environ.get("GOOGLE_API_KEY", "").strip()
            or os.environ.get("GEMINI_API_KEY", "").strip()
        )
        if not key:
            raise RuntimeError(
                "Set MODELALIVE_PROBE_API_KEY or GOOGLE_API_KEY to probe Gemini."
            )
        return base, key, resolved

    base = (
        os.environ.get("MODELALIVE_PROBE_BASE_URL", "").strip()
        or os.environ.get("OPENAI_BASE_URL", "").strip()
        or "https://api.openai.com/v1"
    ).rstrip("/")
    key = (
        os.environ.get("MODELALIVE_PROBE_API_KEY", "").strip()
        or os.environ.get("OPENAI_API_KEY", "").strip()
    )
    if not key:
        raise RuntimeError(
            "Set MODELALIVE_PROBE_API_KEY or OPENAI_API_KEY to probe an OpenAI-compatible endpoint."
        )
    return base, key, resolved


def _extract_openai_content(data: dict[str, Any]) -> str:
    return str(data["choices"][0]["message"]["content"]).strip()


def _extract_anthropic_content(data: dict[str, Any]) -> str:
    for block in data.get("content", []):
        if block.get("type") == "text":
            return str(block.get("text", "")).strip()
    return ""


def _extract_google_content(data: dict[str, Any]) -> str:
    candidates = data.get("candidates") or []
    if not candidates:
        return ""
    parts = candidates[0].get("content", {}).get("parts") or []
    texts = [str(part.get("text", "")) for part in parts if "text" in part]
    return "\n".join(texts).strip()


def _probe_once(
    client: Any,
    *,
    backend: ProbeBackend,
    base: str,
    key: str,
    model: str,
    message: str,
    temperature: float,
    max_tokens: int,
) -> str:
    if backend == "anthropic":
        headers = {
            "x-api-key": key,
            "anthropic-version": os.environ.get("ANTHROPIC_VERSION", "2023-06-01"),
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": message}],
        }
        response = client.post(f"{base}/messages", headers=headers, json=payload)
        response.raise_for_status()
        return _extract_anthropic_content(response.json())

    if backend == "google":
        model_path = model.removeprefix("google/")
        url = f"{base}/models/{model_path}:generateContent?key={key}"
        payload = {
            "contents": [{"role": "user", "parts": [{"text": message}]}],
            "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens},
        }
        response = client.post(url, json=payload)
        response.raise_for_status()
        return _extract_google_content(response.json())

    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": message}],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    response = client.post(f"{base}/chat/completions", headers=headers, json=payload)
    response.raise_for_status()
    return _extract_openai_content(response.json())


def probe_responses(
    model: str,
    *,
    samples: int = 1,
    temperature: float = 0.0,
    max_tokens: int = 256,
    timeout: float = 60.0,
    provider: str | None = None,
) -> dict[str, list[str]]:
    try:
        import httpx
    except ImportError as exc:
        raise RuntimeError("Live probe requires httpx — pip install modelalive[http]") from exc

    base, key, backend = probe_config(resolve_probe_backend(model, provider), model)
    out: dict[str, list[str]] = {}

    with httpx.Client(timeout=timeout) as client:
        for spec in list_stable_prompts():
            pid = spec["id"]
            message = spec["message"]
            out[pid] = []
            for _ in range(max(1, samples)):
                out[pid].append(
                    _probe_once(
                        client,
                        backend=backend,
                        base=base,
                        key=key,
                        model=model,
                        message=message,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )
                )

    return out
