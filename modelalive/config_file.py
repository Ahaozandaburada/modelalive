from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[no-redef]


@dataclass
class ProjectConfig:
    models: list[str] = field(default_factory=list)
    strict_unknown: bool = False
    warn_days: int | None = None
    warn_deprecated: bool = False


def load_config(path: str | Path = "modelalive.toml") -> ProjectConfig:
    config_path = Path(path)
    if not config_path.exists():
        return ProjectConfig()

    data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    ci = data.get("ci", {})
    models = data.get("models", [])
    if isinstance(models, str):
        models = [models]
    return ProjectConfig(
        models=list(models),
        strict_unknown=bool(ci.get("strict_unknown", False)),
        warn_days=ci.get("warn_days"),
        warn_deprecated=bool(ci.get("warn_deprecated", False)),
    )
