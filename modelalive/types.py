from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class AliveResult:
    model: str
    alive: bool
    status: str  # active | deprecated | retired | unknown
    provider: str | None = None
    deprecated_at: str | None = None
    retired_at: str | None = None
    replacement: str | None = None
    breaking_changes: list[str] = field(default_factory=list)
    migrate_url: str | None = None
    days_until_retirement: int | None = None
    message: str | None = None
    registry_version: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
