#!/usr/bin/env python3
"""Parse Google Gemini deprecation docs into registry seed entries."""

from __future__ import annotations

import argparse
import json
import re
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GOOGLE_URL = "https://ai.google.dev/gemini-api/docs/deprecations"
MIGRATE_URL = GOOGLE_URL
SEED_OUT = ROOT / "registry" / "seeds" / "google_parsed.json"

HTML_ROW = re.compile(
    r"<td><code[^>]*>(gemini-[a-z0-9._-]+)</code></td>\s*"
    r"<td>([^<]*)</td>\s*"
    r"<td>([^<]*)</td>\s*"
    r"(?:<td><code[^>]*>(gemini-[a-z0-9._-]+)</code></td>|<td>([^<]*)</td>)",
    re.IGNORECASE,
)
DATE_NAMED = re.compile(r"([A-Za-z]+)\s+([0-9]{1,2}),\s*([0-9]{4})")


def fetch_page(url: str = GOOGLE_URL) -> str:
    try:
        import httpx
    except ImportError as exc:
        raise SystemExit("pip install httpx") from exc
    return httpx.get(url, follow_redirects=True, timeout=30.0).text


def parse_date(raw: str) -> str | None:
    text = raw.strip()
    if not text or text.lower() in {"tbd", "—", "-"}:
        return None
    match = DATE_NAMED.search(text)
    if match:
        month, day, year = match.groups()
        for fmt in ("%B %d, %Y", "%b %d, %Y"):
            try:
                return datetime.strptime(f"{month} {day}, {year}", fmt).date().isoformat()
            except ValueError:
                continue
    return None


def parse_models(page: str, *, today: date) -> dict[str, dict]:
    models: dict[str, dict] = {}
    for model_id, _release, shutdown_raw, repl_code, repl_plain in HTML_ROW.findall(page):
        shutdown = parse_date(shutdown_raw)
        replacement = repl_code or (repl_plain.strip() if repl_plain else None)
        if not shutdown or not replacement or not replacement.startswith("gemini-"):
            continue
        try:
            shutdown_date = date.fromisoformat(shutdown)
        except ValueError:
            continue
        status = "retired" if shutdown_date <= today else "deprecated"
        entry: dict = {
            "provider": "google",
            "status": status,
            "retired_at": shutdown,
            "replacement": replacement,
            "breaking_changes": [],
            "migrate_url": MIGRATE_URL,
            "source": "google",
        }
        if status == "deprecated":
            entry["deprecated_at"] = shutdown
        existing = models.get(model_id)
        if existing and existing.get("retired_at", "9999") <= shutdown:
            continue
        models[model_id] = entry
    return models


def ensure_replacement_actives(models: dict[str, dict]) -> None:
    for repl in {e["replacement"] for e in models.values() if e.get("replacement")}:
        if repl not in models:
            models[repl] = {
                "provider": "google",
                "status": "active",
                "replacement": None,
                "breaking_changes": [],
                "migrate_url": MIGRATE_URL,
                "source": "google",
            }


def main() -> int:
    parser = argparse.ArgumentParser(description="Parse Google Gemini deprecations into seed JSON")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--today", default=date.today().isoformat())
    args = parser.parse_args()

    today = date.fromisoformat(args.today)
    page = args.input.read_text(encoding="utf-8") if args.input else fetch_page()
    models = parse_models(page, today=today)
    ensure_replacement_actives(models)

    seed = {
        "sources": {"google": {"url": GOOGLE_URL, "checked_at": today.isoformat()}},
        "aliases": {},
        "models": models,
    }
    print(f"Parsed {len(models)} Google models")

    if args.write:
        SEED_OUT.write_text(json.dumps(seed, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Wrote {SEED_OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
