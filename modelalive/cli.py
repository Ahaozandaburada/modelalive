from __future__ import annotations

import argparse
import json
import sys

from modelalive.check import alive, check, resolve
from modelalive.exceptions import ModelDeprecatedError, ModelRetiredError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="modelalive",
        description="Pre-flight check: is this LLM model ID still alive?",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    check_cmd = sub.add_parser("check", help="Check a model ID")
    check_cmd.add_argument("model", help="Model ID to check")
    check_cmd.add_argument(
        "--warn-deprecated",
        action="store_true",
        help="Exit non-zero if model is deprecated",
    )
    check_cmd.add_argument("--json", action="store_true", help="Output JSON")

    resolve_cmd = sub.add_parser("resolve", help="Return best model ID to use")
    resolve_cmd.add_argument("model", help="Model ID to resolve")

    args = parser.parse_args(argv)

    if args.command == "check":
        try:
            result = check(args.model, warn_deprecated=args.warn_deprecated)
        except (ModelRetiredError, ModelDeprecatedError) as exc:
            result = exc.result
            if args.json:
                print(json.dumps(result.to_dict(), indent=2))
            else:
                print(result.message or result.model, file=sys.stderr)
            return 1

        if args.json:
            print(json.dumps(result.to_dict(), indent=2))
        else:
            status = "ALIVE" if result.alive else "DEAD"
            print(f"{status}: {result.model} ({result.status})")
            if result.replacement:
                print(f"  replacement: {result.replacement}")
            if result.breaking_changes:
                print("  breaking_changes:")
                for change in result.breaking_changes:
                    print(f"    - {change}")
        return 0

    if args.command == "resolve":
        print(resolve(args.model))
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
