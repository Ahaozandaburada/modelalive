from __future__ import annotations

import json
import os
from datetime import date, datetime
from functools import lru_cache
from importlib import resources
from pathlib import Path
from typing import Any

from modelalive.lifecycle import days_until, effective_status, parse_date

_REGISTRY_FILENAME = "models.json"
_MAX_ALIAS_DEPTH = 8


def _bundled_registry_text() -> str:
    return resources.files("modelalive.data").joinpath(_REGISTRY_FILENAME).read_text(encoding="utf-8")


def _dev_registry_path() -> Path:
    return Path(__file__).resolve().parent.parent / "registry" / _REGISTRY_FILENAME


def _read_registry_text(path: str | Path | None = None) -> str:
    if path is not None:
        return Path(path).read_text(encoding="utf-8")

    env_path = os.environ.get("MODELALIVE_REGISTRY_PATH", "").strip()
    if env_path:
        return Path(env_path).read_text(encoding="utf-8")

    env_url = os.environ.get("MODELALIVE_REGISTRY_URL", "").strip()
    if env_url:
        try:
            import httpx
        except ImportError as exc:
            raise RuntimeError(
                "MODELALIVE_REGISTRY_URL requires httpx — pip install modelalive[http]"
            ) from exc
        response = httpx.get(env_url, timeout=15.0, follow_redirects=True)
        response.raise_for_status()
        return response.text

    try:
        return _bundled_registry_text()
    except (FileNotFoundError, OSError, TypeError):
        return _dev_registry_path().read_text(encoding="utf-8")


@lru_cache(maxsize=8)
def load_registry(path: str | Path | None = None) -> dict[str, Any]:
    return json.loads(_read_registry_text(path))


def clear_registry_cache() -> None:
    load_registry.cache_clear()


def resolve_alias(
    model: str,
    *,
    registry_path: str | Path | None = None,
) -> tuple[str, list[str]]:
    """Follow alias chain; return canonical model ID and steps taken."""
    registry = load_registry(registry_path)
    aliases: dict[str, str] = registry.get("aliases", {})
    chain: list[str] = [model]
    current = model
    for _ in range(_MAX_ALIAS_DEPTH):
        target = aliases.get(current)
        if target is None:
            return current, chain
        if target in chain:
            raise ValueError(f"Alias cycle detected: {' -> '.join(chain + [target])}")
        chain.append(target)
        current = target
    raise ValueError(f"Alias chain too deep for model: {model}")


def get_model_entry(model: str, *, registry_path: str | Path | None = None) -> dict[str, Any] | None:
    registry = load_registry(registry_path)
    return registry.get("models", {}).get(model)


def get_source(source_key: str, *, registry_path: str | Path | None = None) -> dict[str, Any] | None:
    return load_registry(registry_path).get("sources", {}).get(source_key)


def registry_version(*, registry_path: str | Path | None = None) -> str | None:
    return load_registry(registry_path).get("version")


def registry_hash(*, registry_path: str | Path | None = None) -> str:
    """Stable short hash of registry version + model count for ETag headers."""
    import hashlib

    registry = load_registry(registry_path)
    payload = f"{registry.get('version')}:{len(registry.get('models', {}))}"
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def oldest_source_age_days(*, registry_path: str | Path | None = None, today: date | None = None) -> int | None:
    """Days since the oldest provider source was checked."""
    current = today or date.today()
    ages: list[int] = []
    for meta in load_registry(registry_path).get("sources", {}).values():
        checked = parse_date(meta.get("checked_at"))
        if checked:
            ages.append((current - checked).days)
    return max(ages) if ages else None


def list_models(
    *,
    status: str | None = None,
    provider: str | None = None,
    registry_path: str | Path | None = None,
    today: date | None = None,
) -> dict[str, dict[str, Any]]:
    models = load_registry(registry_path).get("models", {})
    current = today or date.today()
    result: dict[str, dict[str, Any]] = {}
    for model_id, entry in models.items():
        effective = effective_status(entry, today=current)
        if status and effective != status:
            continue
        if provider and entry.get("provider") != provider:
            continue
        result[model_id] = entry
    return result


def _parse_date(value: str | None) -> date | None:
    return parse_date(value)


def days_until(value: str | None, *, today: date | None = None) -> int | None:
    from modelalive.lifecycle import days_until as _days_until

    return _days_until(value, today=today)
