from __future__ import annotations

from datetime import date
from pathlib import Path

from modelalive.exceptions import (
    ModelDeprecatedError,
    ModelExpiringSoonError,
    ModelRetiredError,
    ModelUnknownError,
)
from modelalive.lifecycle import days_until, effective_status
from modelalive.normalize import normalize_model
from modelalive.registry import (
    get_model_entry,
    get_source,
    registry_version,
)
from modelalive.universal import universal_resolve
from modelalive.settings import (
    default_strict_unknown,
    default_warn_days,
    default_warn_deprecated,
)
from modelalive.types import AliveResult

_MAX_RESOLVE_DEPTH = 12


def alive(
    model: str,
    *,
    registry_path: str | Path | None = None,
    today: date | None = None,
) -> AliveResult:
    """Return lifecycle status for a model ID without raising."""
    queried = normalize_model(model)
    resolved = universal_resolve(model, registry_path=registry_path)
    canonical = resolved.resolved
    alias_chain = resolved.chain
    aliased = canonical != queried or len(alias_chain) > 1
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
    warn_deprecated: bool | None = None,
    strict_unknown: bool | None = None,
    warn_days: int | None = None,
    registry_path: str | Path | None = None,
    today: date | None = None,
) -> AliveResult:
    """Check model lifecycle; raise on retired (and optionally deprecated/unknown/expiring)."""
    if warn_deprecated is None:
        warn_deprecated = default_warn_deprecated()
    if strict_unknown is None:
        strict_unknown = default_strict_unknown()
    if warn_days is None:
        warn_days = default_warn_days()

    result = alive(model, registry_path=registry_path, today=today)

    if strict_unknown and result.status == "unknown":
        raise ModelUnknownError(result)
    if result.status == "retired":
        raise ModelRetiredError(result)
    if warn_deprecated and result.status == "deprecated":
        raise ModelDeprecatedError(result)
    if (
        warn_days is not None
        and result.status == "deprecated"
        and result.days_until_retirement is not None
        and 0 <= result.days_until_retirement <= warn_days
    ):
        raise ModelExpiringSoonError(result)
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
    """Return the best active model ID, following replacement chains."""
    current = normalize_model(model)
    visited: set[str] = set()

    for _ in range(_MAX_RESOLVE_DEPTH):
        if current in visited:
            break
        visited.add(current)

        result = alive(current, registry_path=registry_path, today=today)
        if result.status in {"active", "unknown"}:
            return result.canonical_model or current
        if not result.replacement:
            return result.canonical_model or current

        replacement = result.replacement
        repl = alive(replacement, registry_path=registry_path, today=today)
        if repl.status == "active":
            return replacement
        current = replacement

    final = alive(current, registry_path=registry_path, today=today)
    return final.replacement or final.canonical_model or current


def ensure(
    model: str,
    *,
    warn_deprecated: bool | None = None,
    strict_unknown: bool | None = None,
    warn_days: int | None = None,
    registry_path: str | Path | None = None,
    today: date | None = None,
) -> str:
    """Pre-flight gate: return a safe model ID, raising only when migration is impossible."""
    if warn_deprecated is None:
        warn_deprecated = default_warn_deprecated()
    if strict_unknown is None:
        strict_unknown = default_strict_unknown()
    if warn_days is None:
        warn_days = default_warn_days()

    result = alive(model, registry_path=registry_path, today=today)

    if strict_unknown and result.status == "unknown":
        raise ModelUnknownError(result)
    if result.status == "retired" and not result.replacement:
        raise ModelRetiredError(result)
    if warn_deprecated and result.status == "deprecated":
        raise ModelDeprecatedError(result)
    if (
        warn_days is not None
        and result.status == "deprecated"
        and result.days_until_retirement is not None
        and 0 <= result.days_until_retirement <= warn_days
    ):
        raise ModelExpiringSoonError(result)

    return resolve(model, registry_path=registry_path, today=today)


def resolve_detail(
    model: str,
    *,
    registry_path: str | Path | None = None,
    today: date | None = None,
) -> dict[str, object]:
    """Return resolved model ID and merged breaking_changes from the migration chain."""
    current = normalize_model(model)
    visited: set[str] = set()
    breaking_changes: list[str] = []
    chain: list[str] = []

    for _ in range(_MAX_RESOLVE_DEPTH):
        if current in visited:
            break
        visited.add(current)
        chain.append(current)

        result = alive(current, registry_path=registry_path, today=today)
        for change in result.breaking_changes:
            if change not in breaking_changes:
                breaking_changes.append(change)

        if result.status in {"active", "unknown"}:
            return {
                "queried_model": model,
                "resolved": result.canonical_model or current,
                "chain": chain,
                "breaking_changes": breaking_changes,
            }
        if not result.replacement:
            return {
                "queried_model": model,
                "resolved": result.canonical_model or current,
                "chain": chain,
                "breaking_changes": breaking_changes,
            }

        repl = alive(result.replacement, registry_path=registry_path, today=today)
        if repl.status == "active":
            for change in repl.breaking_changes:
                if change not in breaking_changes:
                    breaking_changes.append(change)
            return {
                "queried_model": model,
                "resolved": result.replacement,
                "chain": chain + [result.replacement],
                "breaking_changes": breaking_changes,
            }
        current = result.replacement

    resolved = resolve(model, registry_path=registry_path, today=today)
    return {
        "queried_model": model,
        "resolved": resolved,
        "chain": chain,
        "breaking_changes": breaking_changes,
    }


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
