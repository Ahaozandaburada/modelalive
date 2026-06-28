from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from modelalive.lifecycle import effective_status, parse_date
from modelalive.registry import load_registry


@dataclass(frozen=True)
class ValidationIssue:
    level: str  # error | warning
    path: str
    message: str


def validate_registry(path: str | Path | None = None) -> list[ValidationIssue]:
    registry = load_registry(path)
    issues: list[ValidationIssue] = []
    models: dict[str, Any] = registry.get("models", {})
    aliases: dict[str, str] = registry.get("aliases", {})
    sources: dict[str, Any] = registry.get("sources", {})

    if registry.get("schema_version", 1) < 2:
        issues.append(ValidationIssue("warning", "schema_version", "Registry schema_version < 2"))

    for key in ("version", "schema_version", "sources", "models"):
        if key not in registry:
            issues.append(ValidationIssue("error", key, f"Missing required field: {key}"))

    for alias, target in aliases.items():
        if target not in models:
            issues.append(ValidationIssue("error", f"aliases.{alias}", f"Alias target not in registry: {target}"))

    today = date.today()

    for model_id, entry in models.items():
        prefix = f"models.{model_id}"
        status = entry.get("status")
        source_key = entry.get("source")

        if source_key and source_key not in sources:
            issues.append(ValidationIssue("error", prefix, f"Unknown source key: {source_key}"))

        if status in {"deprecated", "retired"} and not entry.get("replacement"):
            issues.append(ValidationIssue("error", prefix, f"{status} model must have replacement"))

        if status == "retired" and not entry.get("retired_at"):
            issues.append(ValidationIssue("error", prefix, "Retired model must have retired_at"))

        if status == "deprecated" and not entry.get("retired_at"):
            issues.append(ValidationIssue("error", prefix, "Deprecated model must have retired_at"))

        retired_at = parse_date(entry.get("retired_at"))
        deprecated_at = parse_date(entry.get("deprecated_at"))
        if retired_at and deprecated_at and deprecated_at > retired_at:
            issues.append(ValidationIssue("error", prefix, "deprecated_at cannot be after retired_at"))

        replacement = entry.get("replacement")
        if replacement and replacement not in models:
            issues.append(
                ValidationIssue(
                    "warning",
                    prefix,
                    f"Replacement {replacement!r} is not in registry (may be intentional)",
                )
            )

        computed = effective_status(entry, today=today)
        if status == "deprecated" and computed == "retired":
            issues.append(
                ValidationIssue(
                    "error",
                    prefix,
                    "status is deprecated but retired_at is in the past — must be retired",
                )
            )
        if status == "active" and computed == "retired":
            issues.append(
                ValidationIssue("error", prefix, "status is active but retired_at is in the past"),
            )

        if replacement and replacement in models:
            repl_status = effective_status(models[replacement], today=today)
            if repl_status == "retired":
                issues.append(
                    ValidationIssue(
                        "error",
                        prefix,
                        f"replacement {replacement!r} is retired — fix replacement chain",
                    )
                )

    for model_id, entry in models.items():
        if entry.get("status") not in {"deprecated", "retired"}:
            continue
        replacement = entry.get("replacement")
        if not replacement:
            continue
        prefix = f"models.{model_id}"
        from modelalive.check import resolve

        try:
            resolved = resolve(model_id, today=today)
        except Exception as exc:  # noqa: BLE001
            issues.append(ValidationIssue("error", prefix, f"resolve failed: {exc}"))
            continue
        resolved_entry = models.get(resolved)
        if resolved_entry is None:
            issues.append(
                ValidationIssue(
                    "warning",
                    prefix,
                    f"replacement chain ends at unlisted model {resolved!r}",
                )
            )
        elif effective_status(resolved_entry, today=today) != "active":
            issues.append(
                ValidationIssue(
                    "error",
                    prefix,
                    f"replacement chain ends at non-active model {resolved!r}",
                )
            )

    return issues


def assert_registry_valid(path: str | Path | None = None) -> None:
    issues = validate_registry(path)
    errors = [issue for issue in issues if issue.level == "error"]
    if errors:
        lines = "\n".join(f"  [{issue.level}] {issue.path}: {issue.message}" for issue in errors)
        raise ValueError(f"Registry validation failed:\n{lines}")
