#!/usr/bin/env python3
"""Parse Fireworks AI changelog deprecations into registry seed entries."""

from __future__ import annotations

import argparse
import json
import re
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIREWORKS_URL = "https://docs.fireworks.ai/updates/changelog.md"
MIGRATE_URL = "https://docs.fireworks.ai/updates/changelog"
SEED_OUT = ROOT / "registry" / "seeds" / "fireworks_parsed.json"

FW_ID = re.compile(r"fireworks/([a-z0-9._-]+)", re.IGNORECASE)
DATE_NAMED = re.compile(r"([A-Za-z]+)\s+([0-9]{1,2}),\s*([0-9]{4})")
DATE_ISO = re.compile(r"([0-9]{4})-([0-9]{2})-([0-9]{2})")

# Human names in changelog → canonical fireworks/ IDs (manual seed wins on merge)
NAME_TO_ID: dict[str, str] = {
    "DeepSeek V3.1": "fireworks/deepseek-v3p1",
    "DeepSeek V3.2": "fireworks/deepseek-v3p2",
    "GLM 4.7": "fireworks/glm-4p7",
    "GLM 5": "fireworks/glm-5",
    "Qwen3 8B": "fireworks/qwen3-8b",
    "Qwen3 VL 30B A3B Thinking": "fireworks/qwen3-vl-30b-a3b-thinking",
    "Qwen3 VL 30B A3B Instruct": "fireworks/qwen3-vl-30b-a3b-instruct",
    "Llama 3.3 70B Instruct": "fireworks/llama-v3p3-70b-instruct",
    "Kimi K2.5": "fireworks/kimi-k2p5",
    "Qwen 3.6 Plus": "fireworks/qwen3p6-plus",
    "MiniMax M2.5": "fireworks/minimax-m2p5",
}


def fetch_page(url: str = FIREWORKS_URL) -> str:
    try:
        import httpx
    except ImportError as exc:
        raise SystemExit("pip install httpx") from exc
    return httpx.get(url, follow_redirects=True, timeout=30.0).text


def parse_date(raw: str) -> str | None:
    text = raw.strip()
    match = DATE_ISO.search(text)
    if match:
        return match.group(0)
    match = DATE_NAMED.search(text)
    if match:
        month, day, year = match.groups()
        for fmt in ("%B %d, %Y", "%b %d, %Y"):
            try:
                return datetime.strptime(f"{month} {day}, {year}", fmt).date().isoformat()
            except ValueError:
                continue
    return None


def canonical_id(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("fireworks/"):
        return raw
    if "/" not in raw:
        return f"fireworks/{raw}"
    return raw


def parse_deprecations(page: str, *, today: date) -> dict[str, dict]:
    models: dict[str, dict] = {}
    current_date: str | None = None

    for line in page.splitlines():
        section_date = parse_date(line)
        if section_date and ("decommission" in line.lower() or "deprecated" in line.lower() or "2026" in line):
            current_date = section_date

        lower = line.lower()
        if "migrate to" not in lower:
            continue

        # Extract first fireworks replacement from line
        fw_ids = FW_ID.findall(line)
        if not fw_ids:
            continue
        replacement = canonical_id(fw_ids[-1])

        model_id: str | None = None
        if fw_ids and "migrate to" in lower:
            # Source may appear as link before "migrate to"
            before, _, _after = line.partition("migrate to")
            src_ids = FW_ID.findall(before)
            if src_ids:
                model_id = canonical_id(src_ids[-1])

        if not model_id:
            for name, mid in NAME_TO_ID.items():
                if name.lower() in line.lower():
                    model_id = mid
                    break

        if not model_id:
            continue

        retired_at = current_date or "2026-07-01"
        try:
            retired_date = date.fromisoformat(retired_at)
        except ValueError:
            continue
        status = "retired" if retired_date <= today else "deprecated"

        entry: dict = {
            "provider": "fireworks",
            "status": status,
            "retired_at": retired_at,
            "replacement": replacement,
            "breaking_changes": ["Fireworks serverless deprecated — see changelog migration guide"],
            "migrate_url": MIGRATE_URL,
            "source": "fireworks",
        }
        if status == "deprecated":
            entry["deprecated_at"] = retired_at

        existing = models.get(model_id)
        if existing and existing.get("retired_at", "9999") <= retired_at:
            continue
        models[model_id] = entry

    return models


def ensure_active_models(models: dict[str, dict]) -> None:
    for repl in {e["replacement"] for e in models.values() if e.get("replacement")}:
        if repl not in models:
            models[repl] = {
                "provider": "fireworks",
                "status": "active",
                "replacement": None,
                "breaking_changes": [],
                "migrate_url": MIGRATE_URL,
                "source": "fireworks",
            }


def main() -> int:
    parser = argparse.ArgumentParser(description="Parse Fireworks changelog into seed JSON")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--today", default=date.today().isoformat())
    args = parser.parse_args()

    today = date.fromisoformat(args.today)
    page = args.input.read_text(encoding="utf-8") if args.input else fetch_page()
    models = parse_deprecations(page, today=today)
    ensure_active_models(models)

    seed = {
        "sources": {"fireworks": {"url": MIGRATE_URL, "checked_at": today.isoformat()}},
        "aliases": {},
        "models": models,
    }
    print(f"Parsed {len(models)} Fireworks models")

    if args.write:
        SEED_OUT.write_text(json.dumps(seed, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Wrote {SEED_OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
