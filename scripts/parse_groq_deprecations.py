#!/usr/bin/env python3
"""Sync Groq deprecation registry from manual seed + doc scrape."""

from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GROQ_URL = "https://console.groq.com/docs/deprecations"
MANUAL = ROOT / "registry" / "seeds" / "groq.json"
SEED_OUT = ROOT / "registry" / "seeds" / "groq_parsed.json"

MODEL_ID = re.compile(r"`([a-z0-9][a-z0-9._-]{2,64})`")
DATE_ISO = re.compile(r"([0-9]{4})-([0-9]{2})-([0-9]{2})")


def fetch_page(url: str = GROQ_URL) -> str:
    try:
        import httpx
    except ImportError as exc:
        raise SystemExit("pip install httpx") from exc
    return httpx.get(url, follow_redirects=True, timeout=30.0).text


def parse_from_html(page: str, *, today: date) -> dict[str, dict]:
    models: dict[str, dict] = {}
    for line in page.splitlines():
        if "retired" not in line.lower() and "deprecated" not in line.lower():
            continue
        ids = MODEL_ID.findall(line)
        if not ids:
            continue
        retired_at = None
        match = DATE_ISO.search(line)
        if match:
            retired_at = match.group(0)
        for model_id in ids:
            if model_id in models:
                continue
            status = "retired" if "retired" in line.lower() else "deprecated"
            entry: dict = {
                "provider": "groq",
                "status": status,
                "breaking_changes": [],
                "migrate_url": GROQ_URL,
                "source": "groq",
            }
            if retired_at:
                entry["retired_at"] = retired_at
            models[model_id] = entry
    return models


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    today = date.today()

    manual = json.loads(MANUAL.read_text(encoding="utf-8"))
    models = dict(manual.get("models", {}))
    aliases = dict(manual.get("aliases", {}))

    if not args.offline:
        try:
            page = fetch_page()
            scraped = parse_from_html(page, today=today)
            for model_id, entry in scraped.items():
                models.setdefault(model_id, entry)
        except Exception as exc:
            print(f"Groq scrape skipped: {exc}")

    seed = {
        "sources": manual.get(
            "sources",
            {"groq": {"url": GROQ_URL, "checked_at": today.isoformat()}},
        ),
        "aliases": aliases,
        "models": models,
    }
    seed["sources"]["groq"]["checked_at"] = today.isoformat()

    if args.write:
        SEED_OUT.write_text(json.dumps(seed, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Wrote {SEED_OUT} ({len(models)} models)")
    else:
        print(json.dumps({"model_count": len(models)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
