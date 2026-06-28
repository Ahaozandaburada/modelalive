from __future__ import annotations

import json
from datetime import date, datetime
from functools import lru_cache
from importlib import resources
from pathlib import Path
from typing import Any

_REGISTRY_FILENAME = "models.json"


def _bundled_registry_text() -> str:
    return resources.files("modelalive.data").joinpath(_REGISTRY_FILENAME).read_text(encoding="utf-8")


def _dev_registry_path() -> Path:
    return Path(__file__).resolve().parent.parent / "registry" / _REGISTRY_FILENAME


@lru_cache(maxsize=1)
def load_registry(path: str | Path | None = None) -> dict[str, Any]:
    if path is not None:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    try:
        return json.loads(_bundled_registry_text())
    except (FileNotFoundError, OSError, TypeError):
        return json.loads(_dev_registry_path().read_text(encoding="utf-8"))


def get_model_entry(model: str, *, registry_path: str | Path | None = None) -> dict[str, Any] | None:
    registry = load_registry(registry_path)
    return registry.get("models", {}).get(model)


def registry_version(*, registry_path: str | Path | None = None) -> str | None:
    return load_registry(registry_path).get("version")


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()


def days_until(value: str | None, *, today: date | None = None) -> int | None:
    target = _parse_date(value)
    if target is None:
        return None
    current = today or date.today()
    return (target - current).days
