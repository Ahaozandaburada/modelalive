from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from modelalive.check import alive, check, ensure, resolve
from modelalive.exceptions import ModelDeprecatedError, ModelRetiredError, ModelUnknownError
from modelalive.registry import list_models, load_registry
from modelalive.validate import assert_registry_valid, validate_registry


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="modelalive",
        description="Pre-flight check: is this LLM model ID still alive?",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    check_cmd = sub.add_parser("check", help="Check one or more model IDs")
    check_cmd.add_argument("models", nargs="+", help="Model ID(s) to check")
    check_cmd.add_argument(
        "--warn-deprecated",
        action="store_true",
        help="Exit non-zero if any model is deprecated",
    )
    check_cmd.add_argument(
        "--strict-unknown",
        action="store_true",
        help="Exit non-zero if any model is not in the registry",
    )
    check_cmd.add_argument("--json", action="store_true", help="Output JSON")

    ensure_cmd = sub.add_parser("ensure", help="Pre-flight: validate and print safe model ID")
    ensure_cmd.add_argument("model", help="Model ID to ensure")
    ensure_cmd.add_argument("--warn-deprecated", action="store_true")
    ensure_cmd.add_argument("--strict-unknown", action="store_true")

    resolve_cmd = sub.add_parser("resolve", help="Return best model ID to use")
    resolve_cmd.add_argument("model", help="Model ID to resolve")

    info_cmd = sub.add_parser("info", help="Show full lifecycle info for one model")
    info_cmd.add_argument("model", help="Model ID")

    list_cmd = sub.add_parser("list", help="List models in registry")
    list_cmd.add_argument("--status", choices=["active", "deprecated", "retired", "legacy"])
    list_cmd.add_argument("--provider", choices=["anthropic", "openai", "google"])
    list_cmd.add_argument("--json", action="store_true")

    validate_cmd = sub.add_parser("validate", help="Validate registry JSON")
    validate_cmd.add_argument("--registry", type=Path, default=None)
    validate_cmd.add_argument("--strict", action="store_true", help="Treat warnings as errors")

    args = parser.parse_args(argv)

    commands = {
        "check": lambda: _cmd_check(args),
        "ensure": lambda: _cmd_ensure(args),
        "resolve": lambda: _cmd_resolve(args),
        "info": lambda: _cmd_info(args),
        "list": lambda: _cmd_list(args),
        "validate": lambda: _cmd_validate(args),
    }
    return commands[args.command]()


def _cmd_check(args: argparse.Namespace) -> int:
    exit_code = 0
    results = []

    for model_arg in args.models:
        try:
            results.append(
                check(
                    model_arg,
                    warn_deprecated=args.warn_deprecated,
                    strict_unknown=args.strict_unknown,
                )
            )
        except (ModelRetiredError, ModelDeprecatedError, ModelUnknownError) as exc:
            results.append(exc.result)
            exit_code = 1

    if args.json:
        print(json.dumps([result.to_dict() for result in results], indent=2))
        return exit_code

    for result in results:
        _print_result(result)
    return exit_code


def _cmd_ensure(args: argparse.Namespace) -> int:
    try:
        print(
            ensure(
                args.model,
                warn_deprecated=args.warn_deprecated,
                strict_unknown=args.strict_unknown,
            )
        )
        return 0
    except (ModelRetiredError, ModelDeprecatedError, ModelUnknownError) as exc:
        print(exc.result.message or str(exc), file=sys.stderr)
        return 1


def _cmd_resolve(args: argparse.Namespace) -> int:
    print(resolve(args.model))
    return 0


def _cmd_info(args: argparse.Namespace) -> int:
    result = alive(args.model)
    print(json.dumps(result.to_dict(), indent=2))
    return 0


def _print_result(result) -> None:
    status = "ALIVE" if result.alive else "DEAD"
    alias = f" (via alias -> {result.canonical_model})" if result.aliased else ""
    queried = result.queried_model or result.model
    print(f"{status}: {queried}{alias} [{result.status}]")
    if result.replacement:
        print(f"  replacement: {result.replacement}")
        print(f"  resolved:    {resolve(queried)}")
    if result.source_url:
        print(f"  source: {result.source_url} (checked {result.source_checked_at})")
    if result.breaking_changes:
        print("  breaking_changes:")
        for change in result.breaking_changes:
            print(f"    - {change}")
    if result.message and result.status in {"retired", "deprecated", "unknown"}:
        print(f"  note: {result.message}")


def _cmd_list(args: argparse.Namespace) -> int:
    models = list_models(status=args.status, provider=args.provider)
    if args.json:
        registry = load_registry()
        print(
            json.dumps(
                {
                    "registry_version": registry.get("version"),
                    "count": len(models),
                    "models": models,
                },
                indent=2,
            )
        )
        return 0

    print(f"Registry {load_registry().get('version')} — {len(models)} model(s)")
    for model_id, entry in sorted(models.items()):
        replacement = entry.get("replacement")
        suffix = f" -> {replacement}" if replacement else ""
        print(f"  {model_id:40} {entry.get('status'):12} [{entry.get('provider')}]{suffix}")
    return 0


def _cmd_validate(args: argparse.Namespace) -> int:
    try:
        assert_registry_valid(args.registry)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    issues = validate_registry(args.registry)
    warnings = [issue for issue in issues if issue.level == "warning"]
    for issue in issues:
        print(f"[{issue.level}] {issue.path}: {issue.message}")

    if args.strict and warnings:
        return 1
    if any(issue.level == "error" for issue in issues):
        return 1
    print("Registry OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
