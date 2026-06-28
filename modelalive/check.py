from __future__ import annotations

from datetime import date
from pathlib import Path

from modelalive.exceptions import ModelDeprecatedError, ModelRetiredError
from modelalive.registry import days_until, get_model_entry, registry_version
from modelalive.types import AliveResult


def alive(
    model: str,
    *,
    registry_path: str | Path | None = None,
    today: date | None = None,
) -> AliveResult:
    """Return lifecycle status for a model ID without raising."""
    entry = get_model_entry(model, registry_path=registry_path)
    version = registry_version(registry_path=registry_path)

    if entry is None:
        return AliveResult(
            model=model,
            alive=True,
            status="unknown",
            message="Model not in registry — assumed alive. Register at modelalive.dev or pin a known ID.",
            registry_version=version,
        )

    status = entry.get("status", "unknown")
    retired_at = entry.get("retired_at")
    days_left = days_until(retired_at, today=today)

    if status == "retired":
        return AliveResult(
            model=model,
            alive=False,
            status="retired",
            provider=entry.get("provider"),
            deprecated_at=entry.get("deprecated_at"),
            retired_at=retired_at,
            replacement=entry.get("replacement"),
            breaking_changes=list(entry.get("breaking_changes") or []),
            migrate_url=entry.get("migrate_url"),
            days_until_retirement=days_left,
            message=_retired_message(model, entry),
            registry_version=version,
        )

    if status == "deprecated":
        return AliveResult(
            model=model,
            alive=True,
            status="deprecated",
            provider=entry.get("provider"),
            deprecated_at=entry.get("deprecated_at"),
            retired_at=retired_at,
            replacement=entry.get("replacement"),
            breaking_changes=list(entry.get("breaking_changes") or []),
            migrate_url=entry.get("migrate_url"),
            days_until_retirement=days_left,
            message=_deprecated_message(model, entry, days_left),
            registry_version=version,
        )

    return AliveResult(
        model=model,
        alive=True,
        status="active",
        provider=entry.get("provider"),
        replacement=entry.get("replacement"),
        breaking_changes=list(entry.get("breaking_changes") or []),
        migrate_url=entry.get("migrate_url"),
        registry_version=version,
    )


def check(
    model: str,
    *,
    warn_deprecated: bool = False,
    registry_path: str | Path | None = None,
    today: date | None = None,
) -> AliveResult:
    """Check model lifecycle; raise on retired (and optionally deprecated)."""
    result = alive(model, registry_path=registry_path, today=today)

    if result.status == "retired":
        raise ModelRetiredError(result)
    if warn_deprecated and result.status == "deprecated":
        raise ModelDeprecatedError(result)
    return result


def resolve(
    model: str,
    *,
    registry_path: str | Path | None = None,
    today: date | None = None,
) -> str:
    """Return replacement model ID if retired/deprecated, else the original."""
    result = alive(model, registry_path=registry_path, today=today)
    if result.replacement:
        return result.replacement
    return model


def _retired_message(model: str, entry: dict) -> str:
    replacement = entry.get("replacement")
    if replacement:
        return f"Model '{model}' was retired. Use '{replacement}' instead."
    return f"Model '{model}' was retired."


def _deprecated_message(model: str, entry: dict, days_left: int | None) -> str:
    replacement = entry.get("replacement")
    retired_at = entry.get("retired_at")
    parts = [f"Model '{model}' is deprecated."]
    if retired_at:
        parts.append(f"Retires on {retired_at}.")
    if days_left is not None and days_left >= 0:
        parts.append(f"{days_left} day(s) remaining.")
    if replacement:
        parts.append(f"Migrate to '{replacement}'.")
    return " ".join(parts)
