from __future__ import annotations

from datetime import date, datetime
from typing import Any


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()


def effective_status(entry: dict[str, Any], *, today: date | None = None) -> str:
    """Derive lifecycle status, applying retirement dates even if registry lags."""
    current = today or date.today()
    retired_at = parse_date(entry.get("retired_at"))
    if retired_at is not None and retired_at <= current:
        return "retired"
    status = entry.get("status", "unknown")
    if status == "legacy":
        return "deprecated"
    return status


def days_until(value: str | None, *, today: date | None = None) -> int | None:
    target = parse_date(value)
    if target is None:
        return None
    current = today or date.today()
    return (target - current).days
