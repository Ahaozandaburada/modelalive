#!/usr/bin/env python3
"""Parse Mistral model docs into registry seed entries."""

from __future__ import annotations

import argparse
import json
import re
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MISTRAL_URL = "https://docs.mistral.ai/getting-started/models/models_overview/"
MANUAL = ROOT / "registry" / "seeds" / "mistral.json"
SEED_OUT = ROOT / "registry" / "seeds" / "mistral_parsed.json"

MISTRAL_ID = re.compile(r"\b(mistral-[a-z0-9-]+|open-mistral-[a-z0-9-]+|pixtral-[a-z0-9-]+)\b")
DATE_NAMED = re.compile(r"([A-Za-z]+)\s+([0-9]{1,2}),?\s*([0-9]{4})")


def fetch_page(url: str = MISTRAL_URL) -> str:
    try:
        import httpx
    except ImportError as exc:
        raise SystemExit("pip install httpx") from exc
    return httpx.get(url, follow_redirects=True, timeout=30.0).text


def parse_date(raw: str) -> str | None:
    match = DATE_NAMED.search(raw)
    if not match:
        return None
    month, day, year = match.groups()
    for fmt in ("%B %d %Y", "%b %d %Y", "%B %d, %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(f"{month} {day} {year}", fmt).date().isoformat()
        except ValueError:
            continue
    return None


def parse_page(page: str, *, today: date) -> dict[str, dict]:
    models: dict[str, dict] = {}
    for line in page.splitlines():
        lower = line.lower()
        if not any(k in lower for k in ("deprecated", "retired", "legacy", "end of life")):
            continue
        ids = MISTRAL_ID.findall(line)
        if not ids:
            continue
        retired_at = parse_date(line)
        for model_id in ids:
            if model_id.endswith("-latest"):
                continue
            status = "retired" if "retired" in lower or "end of life" in lower else "deprecated"
            entry: dict = {
                "provider": "mistral",
                "status": status,
                "breaking_changes": [],
                "migrate_url": MISTRAL_URL,
                "source": "mistral",
            }
            if retired_at:
                if status == "deprecated":
                    entry["deprecated_at"] = retired_at
                else:
                    entry["retired_at"] = retired_at
            models.setdefault(model_id, entry)
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
            scraped = parse_page(page, today=today)
            for model_id, entry in scraped.items():
                if model_id in models:
                    models[model_id].update({k: v for k, v in entry.items() if v})
                else:
                    models[model_id] = entry
        except Exception as exc:
            print(f"Mistral scrape skipped: {exc}")

    seed = {
        "sources": manual.get(
            "sources",
            {"mistral": {"url": MISTRAL_URL, "checked_at": today.isoformat()}},
        ),
        "aliases": aliases,
        "models": models,
    }
    seed["sources"]["mistral"]["checked_at"] = today.isoformat()

    if args.write:
        SEED_OUT.write_text(json.dumps(seed, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Wrote {SEED_OUT} ({len(models)} models)")
    else:
        print(json.dumps({"model_count": len(models)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
