from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from modelalive.providers import list_provider_keys, provider_label
from modelalive.config_file import load_config
from modelalive.check import alive, check, ensure, resolve
from modelalive.exceptions import (
    ModelDeprecatedError,
    ModelExpiringSoonError,
    ModelRetiredError,
    ModelUnknownError,
    StableShiftError,
)
from modelalive.expiring import list_expiring
from modelalive.registry import list_models, load_registry
from modelalive.scan import scan_path
from modelalive.settings import default_strict_unknown, default_warn_days, default_warn_deprecated
from modelalive.validate import assert_registry_valid, validate_registry


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="modelalive",
        description="Universal LLM pre-flight gate — Alive (lifecycle) + Stable (behavioral drift)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    check_cmd = sub.add_parser("check", help="Check one or more model IDs")
    check_cmd.add_argument("models", nargs="+", help="Model ID(s) to check")
    check_cmd.add_argument(
        "--warn-deprecated",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Exit non-zero if any model is deprecated (default: $MODELALIVE_WARN_DEPRECATED)",
    )
    check_cmd.add_argument(
        "--strict-unknown",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Exit non-zero if any model is not in the registry (default: $MODELALIVE_STRICT)",
    )
    check_cmd.add_argument(
        "--warn-days",
        type=int,
        default=None,
        help="Fail if model retires within N days",
    )
    check_cmd.add_argument("--json", action="store_true", help="Output JSON")

    ensure_cmd = sub.add_parser("ensure", help="Pre-flight: validate and print safe model ID")
    ensure_cmd.add_argument("model", help="Model ID to ensure")
    ensure_cmd.add_argument("--warn-deprecated", action=argparse.BooleanOptionalAction, default=None)
    ensure_cmd.add_argument("--strict-unknown", action=argparse.BooleanOptionalAction, default=None)
    ensure_cmd.add_argument("--warn-days", type=int, default=None)

    resolve_cmd = sub.add_parser("resolve", help="Return best model ID to use")
    resolve_cmd.add_argument("model", help="Model ID to resolve")

    info_cmd = sub.add_parser("info", help="Show full lifecycle info for one model")
    info_cmd.add_argument("model", help="Model ID")

    list_cmd = sub.add_parser("list", help="List models in registry")
    list_cmd.add_argument("--status", choices=["active", "deprecated", "retired", "legacy"])
    list_cmd.add_argument("--provider", help="Filter by provider (see: modelalive providers)")
    list_cmd.add_argument("--json", action="store_true")

    providers_cmd = sub.add_parser("providers", help="List supported inference providers")
    providers_cmd.add_argument("--json", action="store_true")

    validate_cmd = sub.add_parser("validate", help="Validate registry JSON")
    validate_cmd.add_argument("--registry", type=Path, default=None)
    validate_cmd.add_argument("--strict", action="store_true", help="Treat warnings as errors")

    expiring_cmd = sub.add_parser("expiring", help="List models retiring soon")
    expiring_cmd.add_argument("--days", type=int, default=30)
    expiring_cmd.add_argument("--provider", help="Filter by provider")
    expiring_cmd.add_argument("--json", action="store_true")

    scan_cmd = sub.add_parser("scan", help="Scan project for hardcoded model IDs")
    scan_cmd.add_argument("path", nargs="?", default=".", help="Directory to scan")
    scan_cmd.add_argument("--json", action="store_true")

    config_cmd = sub.add_parser("check-config", help="Check models listed in modelalive.toml")
    config_cmd.add_argument("--file", default="modelalive.toml")

    stable_cmd = sub.add_parser("stable", help="Behavioral stability — detect ghost endpoint drift")
    stable_sub = stable_cmd.add_subparsers(dest="stable_command", required=True)

    stable_prompts = stable_sub.add_parser("prompts", help="List fingerprint probe prompts")
    stable_prompts.add_argument("--json", action="store_true")

    stable_baseline = stable_sub.add_parser("baseline", help="Record behavioral fingerprint baseline")
    stable_baseline.add_argument("model", help="Model ID to probe")
    stable_baseline.add_argument("-o", "--output", default=".modelalive/stable.json")
    stable_baseline.add_argument("--samples", type=int, default=1)
    stable_baseline.add_argument("--provider", choices=["anthropic", "google", "openai", "bedrock", "openrouter"], default=None)
    stable_baseline.add_argument("--from-json", dest="from_json", help="Use saved responses JSON instead of live probe")

    stable_check = stable_sub.add_parser("check", help="Compare live fingerprint to baseline")
    stable_check.add_argument("model", help="Model ID to probe")
    stable_check.add_argument("-b", "--baseline", default=".modelalive/stable.json")
    stable_check.add_argument("--threshold", type=float, default=0.25)
    stable_check.add_argument("--samples", type=int, default=1)
    stable_check.add_argument("--provider", choices=["anthropic", "google", "openai", "bedrock", "openrouter"], default=None)
    stable_check.add_argument("--from-json", dest="from_json", help="Use saved responses JSON instead of live probe")
    stable_check.add_argument("--json", action="store_true")

    stable_diff = stable_sub.add_parser("diff", help="Compare two fingerprint files offline")
    stable_diff.add_argument("baseline", help="Baseline fingerprint JSON")
    stable_diff.add_argument("current", help="Current fingerprint JSON")
    stable_diff.add_argument("--threshold", type=float, default=0.25)
    stable_diff.add_argument("--json", action="store_true")

    stable_validate = stable_sub.add_parser("validate", help="Validate a fingerprint JSON file")
    stable_validate.add_argument("path", help="Fingerprint JSON path")
    stable_validate.add_argument("--json", action="store_true")

    args = parser.parse_args(argv)

    commands = {
        "check": lambda: _cmd_check(args),
        "ensure": lambda: _cmd_ensure(args),
        "resolve": lambda: _cmd_resolve(args),
        "info": lambda: _cmd_info(args),
        "list": lambda: _cmd_list(args),
        "providers": lambda: _cmd_providers(args),
        "validate": lambda: _cmd_validate(args),
        "expiring": lambda: _cmd_expiring(args),
        "scan": lambda: _cmd_scan(args),
        "check-config": lambda: _cmd_check_config(args),
        "stable": lambda: _cmd_stable(args),
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
                    warn_days=args.warn_days,
                )
            )
        except (ModelRetiredError, ModelDeprecatedError, ModelUnknownError, ModelExpiringSoonError) as exc:
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
                warn_days=args.warn_days,
            )
        )
        return 0
    except (ModelRetiredError, ModelDeprecatedError, ModelUnknownError, ModelExpiringSoonError) as exc:
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


def _cmd_providers(args: argparse.Namespace) -> int:
    keys = list_provider_keys()
    if args.json:
        print(json.dumps({"count": len(keys), "providers": {k: provider_label(k) for k in keys}}, indent=2))
        return 0
    print(f"Supported providers ({len(keys)}):")
    for key in keys:
        print(f"  {key:14} {provider_label(key)}")
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


def _cmd_expiring(args: argparse.Namespace) -> int:
    results = list_expiring(within_days=args.days, provider=args.provider)
    if args.json:
        print(json.dumps([r.to_dict() for r in results], indent=2))
        return 0
    print(f"Expiring within {args.days} day(s) — {len(results)} model(s)")
    for result in results:
        print(
            f"  {result.model:40} {result.days_until_retirement:3}d  -> {result.replacement}"
        )
    return 0


def _cmd_scan(args: argparse.Namespace) -> int:
    report = scan_path(args.path)
    if args.json:
        print(
            json.dumps(
                {
                    "root": report.root,
                    "scanned_files": report.scanned_files,
                    "findings": [f.__dict__ for f in report.findings],
                },
                indent=2,
            )
        )
    else:
        print(f"Scanned {report.scanned_files} files under {report.root}")
        if not report.findings:
            print("No retired/deprecated/unknown model IDs found.")
            return 0
        for finding in report.findings:
            repl = f" -> {finding.replacement}" if finding.replacement else ""
            print(f"  {finding.path}:{finding.line}  {finding.model} [{finding.status}]{repl}")
    return 1 if report.findings else 0


def _flag(value: bool | None, default_fn) -> bool:
    return value if value is not None else default_fn()


def _load_probe_responses(args: argparse.Namespace, model: str) -> dict[str, list[str]]:
    if args.from_json:
        data = json.loads(Path(args.from_json).read_text(encoding="utf-8"))
        if isinstance(data, dict) and "responses" in data:
            return data["responses"]
        return data
    from modelalive.probe import probe_responses

    return probe_responses(model, samples=args.samples, provider=getattr(args, "provider", None))


def _cmd_stable(args: argparse.Namespace) -> int:
    from modelalive.stable import Fingerprint, compare_fingerprints, fingerprint_from_responses, list_stable_prompts

    if args.stable_command == "prompts":
        prompts = list_stable_prompts()
        if args.json:
            print(json.dumps(prompts, indent=2))
        else:
            for item in prompts:
                preview = item["message"][:72]
                suffix = "..." if len(item["message"]) > 72 else ""
                print(f"{item['id']}: {preview}{suffix}")
        return 0

    if args.stable_command == "baseline":
        responses = _load_probe_responses(args, args.model)
        endpoint = None
        if not args.from_json:
            try:
                from modelalive.probe import probe_config, resolve_probe_backend

                endpoint, _, backend = probe_config(resolve_probe_backend(args.model, args.provider), args.model)
                print(f"Probed via {backend} → {endpoint}")
            except RuntimeError:
                pass
        fp = fingerprint_from_responses(
            args.model,
            responses,
            endpoint=endpoint,
            samples_per_prompt=args.samples,
        )
        path = fp.save(args.output)
        print(f"Baseline saved → {path} ({len(fp.prompts)} prompts)")
        return 0

    if args.stable_command == "check":
        baseline = Fingerprint.load(args.baseline)
        responses = _load_probe_responses(args, args.model)
        endpoint = baseline.endpoint
        if not args.from_json:
            try:
                from modelalive.probe import probe_config, resolve_probe_backend

                endpoint, _, _backend = probe_config(resolve_probe_backend(args.model, args.provider), args.model)
            except RuntimeError:
                pass
        current = fingerprint_from_responses(
            args.model,
            responses,
            endpoint=endpoint,
            samples_per_prompt=args.samples,
        )
        report = compare_fingerprints(baseline, current, threshold=args.threshold)
        if args.json:
            print(json.dumps(report.to_dict(), indent=2))
        else:
            status = "STABLE" if report.stable else "DRIFT"
            print(f"{status}: {args.model}  mean={report.mean_distance:.3f}  max={report.max_distance:.3f}")
            for shift in report.prompt_shifts:
                print(f"  shifted {shift.prompt_id}: {shift.distance:.3f}")
        return 0 if report.stable else 1

    if args.stable_command == "diff":
        baseline = Fingerprint.load(args.baseline)
        current = Fingerprint.load(args.current)
        report = compare_fingerprints(baseline, current, threshold=args.threshold)
        if args.json:
            print(json.dumps(report.to_dict(), indent=2))
        else:
            status = "STABLE" if report.stable else "DRIFT"
            print(f"{status}: mean={report.mean_distance:.3f}  max={report.max_distance:.3f}")
            for shift in report.prompt_shifts:
                print(f"  shifted {shift.prompt_id}: {shift.distance:.3f}")
        return 0 if report.stable else 1

    if args.stable_command == "validate":
        from modelalive.stable import validate_fingerprint

        data = json.loads(Path(args.path).read_text(encoding="utf-8"))
        errors = validate_fingerprint(data)
        if args.json:
            print(json.dumps({"valid": not errors, "errors": errors}, indent=2))
        elif errors:
            for err in errors:
                print(f"INVALID: {err}", file=sys.stderr)
        else:
            print(f"Valid fingerprint for {data.get('model')}")
        return 1 if errors else 0

    return 1


def _cmd_check_config(args: argparse.Namespace) -> int:
    config = load_config(args.file)
    if not config.models and not config.stable:
        print(f"No models or [[stable]] entries in {args.file}", file=sys.stderr)
        return 1
    exit_code = 0
    if config.models:
        check_args = argparse.Namespace(
            models=config.models,
            warn_deprecated=_flag(config.warn_deprecated, default_warn_deprecated),
            strict_unknown=_flag(config.strict_unknown, default_strict_unknown),
            warn_days=config.warn_days if config.warn_days is not None else default_warn_days(),
            json=False,
        )
        exit_code = max(exit_code, _cmd_check(check_args))

    if config.stable:
        from modelalive.stable import (
            Fingerprint,
            compare_fingerprints,
            fingerprint_from_responses,
            validate_fingerprint,
        )

        skip_probe = os.environ.get("MODELALIVE_STABLE_SKIP_PROBE", "").strip().lower() in {"1", "true", "yes"}
        for entry in config.stable:
            baseline_path = Path(entry.baseline)
            if not baseline_path.exists():
                print(f"Missing stable baseline: {baseline_path}", file=sys.stderr)
                exit_code = 1
                continue
            data = json.loads(baseline_path.read_text(encoding="utf-8"))
            errors = validate_fingerprint(data)
            if errors:
                print(f"Invalid baseline {baseline_path}: {errors[0]}", file=sys.stderr)
                exit_code = 1
                continue
            baseline = Fingerprint.from_dict(data)
            threshold = entry.threshold if entry.threshold is not None else (config.stable_threshold or 0.25)
            if skip_probe:
                print(f"Stable baseline OK (offline): {entry.model} → {baseline_path}")
                continue
            probe_args = argparse.Namespace(
                from_json=None,
                samples=1,
                provider=entry.provider,
            )
            try:
                responses = _load_probe_responses(probe_args, entry.model)
            except RuntimeError as exc:
                print(f"Stable probe skipped for {entry.model}: {exc}", file=sys.stderr)
                exit_code = 1
                continue
            current = fingerprint_from_responses(entry.model, responses)
            report = compare_fingerprints(baseline, current, threshold=threshold)
            if report.stable:
                print(f"STABLE: {entry.model} mean={report.mean_distance:.3f}")
            else:
                print(f"DRIFT: {entry.model} mean={report.mean_distance:.3f}", file=sys.stderr)
                exit_code = 1
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
