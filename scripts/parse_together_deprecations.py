#!/usr/bin/env python3
"""Parse Together AI deprecation docs into registry seed entries."""

from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOGETHER_URL = "https://docs.together.ai/docs/deprecations.md"
MIGRATE_URL = TOGETHER_URL
SEED_OUT = ROOT / "registry" / "seeds" / "together_parsed.json"
DEFAULT_REPLACEMENT = "MiniMaxAI/MiniMax-M3"

BACKTICK_RE = re.compile(r"`([^`]+)`")
DATE_ISO = re.compile(r"^([0-9]{4})-([0-9]{2})-([0-9]{2})$")


def fetch_page(url: str = TOGETHER_URL) -> str:
    try:
        import httpx
    except ImportError as exc:
        raise SystemExit("pip install httpx") from exc
    return httpx.get(url, follow_redirects=True, timeout=30.0).text


def parse_deprecation_table(page: str, *, today: date) -> dict[str, dict]:
    models: dict[str, dict] = {}
    in_history = False

    for line in page.splitlines():
        if "Deprecation history" in line:
            in_history = True
            continue
        if not in_history or not line.strip().startswith("|"):
            continue
        if "---" in line:
            continue
        parts = [p.strip() for p in line.split("|")[1:-1]]
        if len(parts) < 2:
            continue
        removal_raw = parts[0].strip()
        if not DATE_ISO.match(removal_raw):
            continue
        model_match = BACKTICK_RE.search(parts[1])
        if not model_match:
            continue
        model_id = model_match.group(1).strip()
        if model_id.lower().startswith("coming soon"):
            continue

        removal_date = date.fromisoformat(removal_raw)
        status = "retired" if removal_date <= today else "deprecated"
        entry: dict = {
            "provider": "together",
            "status": status,
            "retired_at": removal_raw,
            "replacement": DEFAULT_REPLACEMENT,
            "breaking_changes": ["Together serverless endpoint removed — see migration options"],
            "migrate_url": MIGRATE_URL,
            "source": "together",
        }
        if status == "deprecated":
            entry["deprecated_at"] = removal_raw

        existing = models.get(model_id)
        if existing and existing.get("retired_at", "9999") <= removal_raw:
            continue
        models[model_id] = entry

    return models


def parse_redirects(page: str) -> dict[str, str]:
    aliases: dict[str, str] = {}
    in_redirects = False
    for line in page.splitlines():
        if "Active model redirects" in line:
            in_redirects = True
            continue
        if in_redirects and line.startswith("## Deprecation policy"):
            break
        if not in_redirects or not line.strip().startswith("|"):
            continue
        if "---" in line or "Original model" in line:
            continue
        parts = [p.strip() for p in line.split("|")[1:-1]]
        if len(parts) < 2:
            continue
        src = BACKTICK_RE.search(parts[0])
        dst = BACKTICK_RE.search(parts[1])
        if src and dst and src.group(1) != dst.group(1):
            aliases[src.group(1)] = dst.group(1)
    return aliases


def ensure_active_models(models: dict[str, dict], aliases: dict[str, str]) -> None:
    needed = {e["replacement"] for e in models.values() if e.get("replacement")}
    needed.update(aliases.values())
    for repl in needed:
        if repl not in models:
            models[repl] = {
                "provider": "together",
                "status": "active",
                "replacement": None,
                "breaking_changes": [],
                "migrate_url": MIGRATE_URL,
                "source": "together",
                "notes": "Together redirect/active endpoint — add lifecycle when deprecated",
            }


def main() -> int:
    parser = argparse.ArgumentParser(description="Parse Together deprecations into seed JSON")
    parser.add_argument("--input", type=Path, help="Local markdown file")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--today", default=date.today().isoformat())
    args = parser.parse_args()

    today = date.fromisoformat(args.today)
    page = args.input.read_text(encoding="utf-8") if args.input else fetch_page()
    models = parse_deprecation_table(page, today=today)
    aliases = parse_redirects(page)
    ensure_active_models(models, aliases)

    seed = {
        "sources": {
            "together": {"url": TOGETHER_URL, "checked_at": today.isoformat()}
        },
        "aliases": aliases,
        "models": models,
    }
    print(f"Parsed {len(models)} models, {len(aliases)} redirects")

    if args.write:
        SEED_OUT.write_text(json.dumps(seed, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Wrote {SEED_OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
