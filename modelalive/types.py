from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class AliveResult:
    model: str
    alive: bool
    status: str  # active | deprecated | retired | unknown
    queried_model: str | None = None
    canonical_model: str | None = None
    aliased: bool = False
    provider: str | None = None
    deprecated_at: str | None = None
    retired_at: str | None = None
    replacement: str | None = None
    breaking_changes: list[str] = field(default_factory=list)
    migrate_url: str | None = None
    days_until_retirement: int | None = None
    message: str | None = None
    registry_version: str | None = None
    source_url: str | None = None
    source_checked_at: str | None = None
    confidence: str = "unknown"  # verified | unknown

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
