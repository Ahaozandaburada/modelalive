from __future__ import annotations

from datetime import date
from pathlib import Path

from modelalive.exceptions import ModelDeprecatedError, ModelRetiredError
from modelalive.normalize import normalize_model
from modelalive.registry import (
    days_until,
    get_model_entry,
    get_source,
    registry_version,
    resolve_alias,
)
from modelalive.types import AliveResult
from modelalive.validate import effective_status


def alive(
    model: str,
    *,
    registry_path: str | Path | None = None,
    today: date | None = None,
) -> AliveResult:
    """Return lifecycle status for a model ID without raising."""
    queried = normalize_model(model)
    canonical, alias_chain = resolve_alias(queried, registry_path=registry_path)
    aliased = len(alias_chain) > 1
    version = registry_version(registry_path=registry_path)

    entry = get_model_entry(canonical, registry_path=registry_path)
    if entry is None:
        return AliveResult(
            model=canonical,
            queried_model=queried,
            canonical_model=canonical,
            aliased=aliased,
            alive=True,
            status="unknown",
            confidence="unknown",
            message=(
                "Model not in registry — assumed alive. "
                "Open an issue to add it: https://github.com/Ahaozandaburada/modelalive/issues"
            ),
            registry_version=version,
        )

    source_meta = get_source(entry.get("source", ""), registry_path=registry_path) or {}
    status = effective_status(entry, today=today)
    retired_at = entry.get("retired_at")
    days_left = days_until(retired_at, today=today)
    is_alive = status in {"active", "deprecated", "legacy", "unknown"}
    confidence = "verified" if entry.get("source") else "unknown"

    base = dict(
        model=canonical,
        queried_model=queried,
        canonical_model=canonical,
        aliased=aliased,
        provider=entry.get("provider"),
        deprecated_at=entry.get("deprecated_at"),
        retired_at=retired_at,
        replacement=entry.get("replacement"),
        breaking_changes=list(entry.get("breaking_changes") or []),
        migrate_url=entry.get("migrate_url"),
        days_until_retirement=days_left,
        registry_version=version,
        source_url=source_meta.get("url"),
        source_checked_at=source_meta.get("checked_at"),
        confidence=confidence,
    )

    if status == "retired":
        return AliveResult(
            **base,
            alive=False,
            status="retired",
            message=_retired_message(canonical, entry, aliased=aliased, queried=queried),
        )

    if status == "deprecated":
        return AliveResult(
            **base,
            alive=True,
            status="deprecated",
            message=_deprecated_message(canonical, entry, days_left, aliased=aliased, queried=queried),
        )

    return AliveResult(
        **base,
        alive=is_alive,
        status="active",
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


def check_many(
    models: list[str],
    *,
    registry_path: str | Path | None = None,
    today: date | None = None,
) -> list[AliveResult]:
    return [alive(model, registry_path=registry_path, today=today) for model in models]


def resolve(
    model: str,
    *,
    registry_path: str | Path | None = None,
    today: date | None = None,
) -> str:
    """Return best model ID to use: replacement if retired/deprecated, else canonical."""
    result = alive(model, registry_path=registry_path, today=today)
    if result.replacement:
        return result.replacement
    return result.canonical_model or result.model


def _retired_message(
    model: str,
    entry: dict,
    *,
    aliased: bool,
    queried: str,
) -> str:
    replacement = entry.get("replacement")
    alias_note = f" (alias {queried!r})" if aliased else ""
    if replacement:
        return f"Model '{model}'{alias_note} was retired. Use '{replacement}' instead."
    return f"Model '{model}'{alias_note} was retired."


def _deprecated_message(
    model: str,
    entry: dict,
    days_left: int | None,
    *,
    aliased: bool,
    queried: str,
) -> str:
    replacement = entry.get("replacement")
    retired_at = entry.get("retired_at")
    alias_note = f" (alias {queried!r})" if aliased else ""
    parts = [f"Model '{model}'{alias_note} is deprecated."]
    if retired_at:
        parts.append(f"Retires on {retired_at}.")
    if days_left is not None and days_left >= 0:
        parts.append(f"{days_left} day(s) remaining.")
    if replacement:
        parts.append(f"Migrate to '{replacement}'.")
    return " ".join(parts)
