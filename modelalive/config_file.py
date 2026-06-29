from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[no-redef]


@dataclass
class StableEntry:
    model: str
    baseline: str
    threshold: float | None = None
    provider: str | None = None


@dataclass
class ProjectConfig:
    models: list[str] = field(default_factory=list)
    strict_unknown: bool | None = None
    warn_days: int | None = None
    warn_deprecated: bool | None = None
    stable: list[StableEntry] = field(default_factory=list)
    stable_threshold: float | None = None


def load_config(path: str | Path = "modelalive.toml") -> ProjectConfig:
    config_path = Path(path)
    if not config_path.exists():
        return ProjectConfig()

    data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    ci = data.get("ci", {})
    models = data.get("models", [])
    if isinstance(models, str):
        models = [models]

    stable_rows = data.get("stable", [])
    stable_entries: list[StableEntry] = []
    if isinstance(stable_rows, dict):
        stable_rows = [stable_rows]
    for row in stable_rows:
        if not isinstance(row, dict) or "model" not in row or "baseline" not in row:
            continue
        stable_entries.append(
            StableEntry(
                model=str(row["model"]),
                baseline=str(row["baseline"]),
                threshold=row.get("threshold"),
                provider=row.get("provider"),
            )
        )

    stable_defaults = data.get("stable_defaults", {})

    return ProjectConfig(
        models=list(models),
        strict_unknown=ci["strict_unknown"] if "strict_unknown" in ci else None,
        warn_days=ci.get("warn_days"),
        warn_deprecated=ci["warn_deprecated"] if "warn_deprecated" in ci else None,
        stable=stable_entries,
        stable_threshold=stable_defaults.get("threshold"),
    )
