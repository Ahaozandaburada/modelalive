from __future__ import annotations

from datetime import date
from pathlib import Path

from modelalive.lifecycle import effective_status, parse_date
from modelalive.registry import load_registry
from modelalive.types import AliveResult
from modelalive.check import alive


def list_expiring(
    *,
    within_days: int = 30,
    provider: str | None = None,
    registry_path: str | Path | None = None,
    today: date | None = None,
) -> list[AliveResult]:
    current = today or date.today()
    registry = load_registry(registry_path)
    results: list[AliveResult] = []

    for model_id, entry in registry.get("models", {}).items():
        if provider and entry.get("provider") != provider:
            continue
        status = effective_status(entry, today=current)
        if status not in {"deprecated", "retired"}:
            continue
        retired_at = parse_date(entry.get("retired_at"))
        if retired_at is None:
            continue
        days_left = (retired_at - current).days
        if status == "retired" or days_left < 0:
            continue
        if days_left <= within_days:
            results.append(alive(model_id, registry_path=registry_path, today=current))

    return sorted(results, key=lambda r: r.days_until_retirement or 0)
