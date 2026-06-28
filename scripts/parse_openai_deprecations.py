#!/usr/bin/env python3
"""Parse OpenAI deprecation docs into registry seed entries."""

from __future__ import annotations

import argparse
import json
import re
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OPENAI_URL = "https://developers.openai.com/api/docs/deprecations"
MIGRATE_URL = OPENAI_URL
SEED_OUT = ROOT / "registry" / "seeds" / "openai_parsed.json"

BACKTICK_RE = re.compile(r"`([a-zA-Z0-9][a-zA-Z0-9._:/-]{1,127})`")
DATE_ISO = re.compile(r"([0-9]{4})[-‑]([0-9]{2})[-‑]([0-9]{2})")
DATE_NAMED = re.compile(r"([A-Za-z]{3,9})\s+([0-9]{1,2}),\s*([0-9]{4})")

SKIP_IDS = {
    "preview",
    "v1/prompts",
    "v1/fine-tunes",
    "v1/fine_tuning/jobs",
    "v1/edits",
    "v1/engines",
    "v1/search",
    "v1/classifications",
    "v1/answers",
    "Videos",
    "API",
    "Assistants",
    "Real-time",
}


def fetch_page(url: str = OPENAI_URL) -> str:
    try:
        import httpx
    except ImportError as exc:
        raise SystemExit("pip install httpx") from exc
    return httpx.get(url, follow_redirects=True, timeout=30.0).text


def parse_shutdown_date(raw: str) -> str | None:
    text = raw.replace("‑", "-").strip()
    if text.lower() in {"shutdown date", "date", "deprecated model", "model / system", "model snapshot"}:
        return None
    match = DATE_ISO.search(text)
    if match:
        y, m, d = match.groups()
        return f"{y}-{m}-{d}"
    match = DATE_NAMED.search(text)
    if match:
        month, day, year = match.groups()
        for fmt in ("%b %d, %Y", "%B %d, %Y"):
            try:
                return datetime.strptime(f"{month} {day}, {year}", fmt).date().isoformat()
            except ValueError:
                continue
    return None


def extract_model_ids(cell: str) -> list[str]:
    ids = BACKTICK_RE.findall(cell)
    return [i for i in ids if i not in SKIP_IDS and not i.startswith("v1/") and i != "---"]


def pick_replacement(ids: list[str]) -> str | None:
    if not ids:
        return None
    return ids[-1]


def parse_models(page: str, *, today: date) -> tuple[dict[str, dict], dict[str, str]]:
    models: dict[str, dict] = {}
    aliases: dict[str, str] = {}

    for line in page.splitlines():
        if not line.strip().startswith("|"):
            continue
        if "---" in line and "Shutdown" not in line:
            continue
        parts = [p.strip() for p in line.split("|")[1:-1]]
        if len(parts) < 3:
            continue

        shutdown = parse_shutdown_date(parts[0])
        if not shutdown:
            continue

        model_ids = extract_model_ids(parts[1])
        if not model_ids:
            # Some rows use plain text model names in col 2
            plain = parts[1].strip().strip("`")
            if plain and plain not in SKIP_IDS and re.match(r"^[a-zA-Z0-9]", plain):
                model_ids = [plain.split()[0]]

        repl_ids = extract_model_ids(parts[2]) if len(parts) > 2 else []
        if not repl_ids and len(parts) > 2:
            plain = parts[2].strip()
            if plain and plain not in {"---", "—"}:
                repl_ids = extract_model_ids(plain)

        if not model_ids:
            continue

        model_id = model_ids[0]
        replacement = pick_replacement(repl_ids) or (model_ids[-1] if len(model_ids) > 1 else None)

        if len(model_ids) >= 2 and model_ids[1] != replacement:
            # Don't create alias if it would reverse an existing documented alias
            if model_ids[1] not in models and model_ids[0] not in aliases:
                aliases[model_id] = model_ids[1]

        if not replacement:
            continue  # skip entries with no migration path (e.g. Sora)

        try:
            shutdown_date = date.fromisoformat(shutdown)
        except ValueError:
            continue

        status = "retired" if shutdown_date <= today else "deprecated"
        entry: dict = {
            "provider": "openai",
            "status": status,
            "migrate_url": MIGRATE_URL,
            "source": "openai",
            "breaking_changes": [],
            "retired_at": shutdown,
            "replacement": replacement,
        }
        if status == "deprecated":
            entry["deprecated_at"] = shutdown

        existing = models.get(model_id)
        if existing and existing.get("retired_at", "9999") <= shutdown:
            continue
        models[model_id] = entry

    return models, aliases


def ensure_replacement_actives(models: dict[str, dict]) -> None:
    for repl in {e["replacement"] for e in models.values() if e.get("replacement")}:
        if repl not in models:
            models[repl] = {
                "provider": "openai",
                "status": "active",
                "replacement": None,
                "breaking_changes": [],
                "migrate_url": MIGRATE_URL,
                "source": "openai",
            }


def main() -> int:
    parser = argparse.ArgumentParser(description="Parse OpenAI deprecations into seed JSON")
    parser.add_argument("--input", type=Path, help="Local markdown/HTML file")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--today", default=date.today().isoformat())
    args = parser.parse_args()

    today = date.fromisoformat(args.today)
    page = args.input.read_text(encoding="utf-8") if args.input else fetch_page()
    models, aliases = parse_models(page, today=today)
    ensure_replacement_actives(models)

    seed = {"sources": {}, "aliases": {}, "models": models}
    print(f"Parsed {len(models)} models, {len(aliases)} aliases")

    if args.write:
        SEED_OUT.write_text(json.dumps(seed, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Wrote {SEED_OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
