from __future__ import annotations

import json
from functools import lru_cache
from importlib import resources
from pathlib import Path
from typing import Any


def _providers_path() -> Path:
    try:
        bundled = resources.files("modelalive.data").joinpath("providers.json")
        if bundled.is_file():
            return Path(str(bundled))
    except (FileNotFoundError, OSError, TypeError):
        pass
    return Path(__file__).resolve().parent.parent / "registry" / "providers.json"


@lru_cache(maxsize=1)
def load_providers_meta() -> dict[str, Any]:
    path = _providers_path()
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"providers": {}}


def list_provider_keys(*, registry_path: str | Path | None = None) -> list[str]:
    from modelalive.registry import load_registry

    registry = load_registry(registry_path)
    keys: set[str] = set(registry.get("sources", {}))
    for entry in registry.get("models", {}).values():
        if entry.get("provider"):
            keys.add(entry["provider"])
    meta = load_providers_meta().get("providers", {})
    keys.update(meta.keys())
    return sorted(keys)


def provider_label(key: str) -> str:
    meta = load_providers_meta().get("providers", {}).get(key, {})
    return meta.get("name") or key
