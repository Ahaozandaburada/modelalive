from __future__ import annotations

import os


def env_flag(name: str, *, default: bool = False) -> bool:
    value = os.environ.get(name, "").strip().lower()
    if not value:
        return default
    return value in {"1", "true", "yes", "on"}


def default_strict_unknown() -> bool:
    return env_flag("MODELALIVE_STRICT", default=False)


def default_warn_deprecated() -> bool:
    return env_flag("MODELALIVE_WARN_DEPRECATED", default=False)


def default_warn_days() -> int | None:
    raw = os.environ.get("MODELALIVE_WARN_DAYS", "").strip()
    if not raw:
        return None
    try:
        return max(0, int(raw))
    except ValueError:
        return None
