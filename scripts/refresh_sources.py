#!/usr/bin/env python3
"""Refresh source checked_at dates and verify model IDs appear on provider pages."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = ROOT / "registry" / "models.json"
BUNDLE_PATH = ROOT / "modelalive" / "data" / "models.json"
MODEL_ID_IN_DOCS = re.compile(r"`([a-zA-Z0-9][a-zA-Z0-9._-]{1,127})`")


def fetch_url(url: str) -> str:
    try:
        import httpx
    except ImportError as exc:
        raise SystemExit("Install httpx: pip install modelalive[http]") from exc

    response = httpx.get(url, follow_redirects=True, timeout=30.0)
    response.raise_for_status()
    return response.text


def models_for_source(registry: dict, source_key: str) -> list[str]:
    return [
        model_id
        for model_id, entry in registry.get("models", {}).items()
        if entry.get("source") == source_key
    ]


def verify_models_on_page(model_ids: list[str], page_text: str) -> list[str]:
    documented = set(MODEL_ID_IN_DOCS.findall(page_text))
    return [model_id for model_id in model_ids if model_id not in documented and model_id not in page_text]


def refresh_registry(*, dry_run: bool = False, skip_fetch: bool = False) -> int:
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    today = date.today().isoformat()
    fetch_errors: list[str] = []
    missing_warnings: list[str] = []

    for source_key, meta in registry.get("sources", {}).items():
        url = meta.get("url")
        if not url:
            fetch_errors.append(f"{source_key}: missing url")
            continue

        if skip_fetch:
            print(f"[skip] {source_key}: would check {url}")
            continue

        print(f"Fetching {source_key} ...")
        try:
            page = fetch_url(url)
        except Exception as exc:  # noqa: BLE001
            missing_warnings.append(f"{source_key}: fetch failed: {exc}")
            meta["checked_at"] = today
            continue

        missing = verify_models_on_page(models_for_source(registry, source_key), page)
        if missing:
            preview = ", ".join(missing[:5])
            suffix = f" (+{len(missing) - 5} more)" if len(missing) > 5 else ""
            missing_warnings.append(f"{source_key}: not found on source page: {preview}{suffix}")

        meta["checked_at"] = today
        print(f"  updated checked_at -> {today}")

    registry["version"] = today

    if dry_run:
        print("Dry run — registry not written.")
        for issue in fetch_errors + missing_warnings:
            print(f"  ! {issue}")
        return 1 if fetch_errors else 0

    REGISTRY_PATH.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    BUNDLE_PATH.write_text(REGISTRY_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"Wrote {REGISTRY_PATH}")

    if missing_warnings:
        print("\nWarnings:")
        for issue in missing_warnings:
            print(f"  ! {issue}")

    if fetch_errors:
        print("\nErrors:")
        for issue in fetch_errors:
            print(f"  ! {issue}")
        return 1

    print("Source refresh complete.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Refresh ModelAlive registry source metadata")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-fetch", action="store_true", help="Only bump dates (offline)")
    args = parser.parse_args()
    return refresh_registry(dry_run=args.dry_run, skip_fetch=args.skip_fetch)


if __name__ == "__main__":
    raise SystemExit(main())
