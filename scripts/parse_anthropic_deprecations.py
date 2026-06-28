#!/usr/bin/env python3
"""Parse Anthropic model deprecation docs into registry seed entries."""

from __future__ import annotations

import argparse
import json
import re
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ANTHROPIC_URL = "https://platform.claude.com/docs/en/about-claude/model-deprecations"
MIGRATE_URL = ANTHROPIC_URL
SEED_OUT = ROOT / "registry" / "seeds" / "anthropic_parsed.json"

BACKTICK_RE = re.compile(r"`([a-zA-Z0-9][a-zA-Z0-9._-]{1,127})`")
CLAUDE_ID_RE = re.compile(r"(claude-[a-z0-9][a-z0-9._-]*)")
DATE_ISO = re.compile(r"([0-9]{4})-([0-9]{2})-([0-9]{2})")
DATE_NAMED = re.compile(r"([A-Za-z]+)\s+([0-9]{1,2}),\s*([0-9]{4})")
HTML_HISTORY_ROW = re.compile(
    r"<td[^>]*>([^<]+)</td>\s*"
    r'<td[^>]*><code[^>]*>([^<]+)</code></td>\s*'
    r'<td[^>]*><code[^>]*>([^<]+)</code></td>',
    re.IGNORECASE,
)
HTML_STATUS_ROW = re.compile(
    r'<td[^>]*>[^<]*<span[^>]*>(claude-[a-z0-9][a-z0-9._-]*)</span></td>'
    r'<td[^>]*>([^<]+)</td>'
    r'<td[^>]*>([^<]*)</td>'
    r'<td[^>]*>([^<]*)</td>',
    re.IGNORECASE,
)


def fetch_page(url: str = ANTHROPIC_URL) -> str:
    try:
        import httpx
    except ImportError as exc:
        raise SystemExit("pip install httpx") from exc
    return httpx.get(url, follow_redirects=True, timeout=30.0).text


def parse_date(raw: str) -> str | None:
    text = raw.strip()
    if not text or text.lower() in {"n/a", "—", "-"}:
        return None
    if "not sooner" in text.lower():
        return None
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


def parse_markdown_tables(page: str, *, today: date) -> tuple[dict[str, dict], dict[str, str]]:
    models: dict[str, dict] = {}
    aliases: dict[str, str] = {}

    for line in page.splitlines():
        if not line.strip().startswith("|"):
            continue
        if "---" in line and "Retirement" not in line:
            continue
        parts = [p.strip() for p in line.split("|")[1:-1]]
        if len(parts) < 3:
            continue

        retired_at = parse_date(parts[0])
        if not retired_at:
            continue

        model_ids = BACKTICK_RE.findall(parts[1]) or CLAUDE_ID_RE.findall(parts[1])
        repl_ids = BACKTICK_RE.findall(parts[2]) if len(parts) > 2 else []
        if not model_ids:
            continue

        model_id = model_ids[0]
        replacement = repl_ids[0] if repl_ids else None
        if not replacement:
            continue

        try:
            retired_date = date.fromisoformat(retired_at)
        except ValueError:
            continue

        status = "retired" if retired_date <= today else "deprecated"
        entry: dict = {
            "provider": "anthropic",
            "status": status,
            "retired_at": retired_at,
            "replacement": replacement,
            "breaking_changes": [],
            "migrate_url": MIGRATE_URL,
            "source": "anthropic",
        }
        if status == "deprecated":
            entry["deprecated_at"] = retired_at

        existing = models.get(model_id)
        if existing and existing.get("retired_at", "9999") <= retired_at:
            continue
        models[model_id] = entry

    return models, aliases


def parse_html_history(page: str, *, today: date) -> dict[str, dict]:
    models: dict[str, dict] = {}
    for date_raw, model_id, replacement in HTML_HISTORY_ROW.findall(page):
        retired_at = parse_date(date_raw)
        if not retired_at or not model_id.startswith("claude-"):
            continue
        try:
            retired_date = date.fromisoformat(retired_at)
        except ValueError:
            continue
        status = "retired" if retired_date <= today else "deprecated"
        entry: dict = {
            "provider": "anthropic",
            "status": status,
            "retired_at": retired_at,
            "replacement": replacement.strip(),
            "breaking_changes": [],
            "migrate_url": MIGRATE_URL,
            "source": "anthropic",
        }
        if status == "deprecated":
            entry["deprecated_at"] = retired_at
        existing = models.get(model_id)
        if existing and existing.get("retired_at", "9999") <= retired_at:
            continue
        models[model_id] = entry
    return models


def parse_html_status(page: str, *, today: date) -> dict[str, dict]:
    models: dict[str, dict] = {}
    for model_id, state_raw, _deprecated_raw, retired_raw in HTML_STATUS_ROW.findall(page):
        state = state_raw.strip().lower()
        if state == "active":
            models[model_id] = {
                "provider": "anthropic",
                "status": "active",
                "replacement": None,
                "breaking_changes": [],
                "migrate_url": MIGRATE_URL,
                "source": "anthropic",
            }
            continue
        retired_at = parse_date(retired_raw)
        if not retired_at:
            continue
        try:
            retired_date = date.fromisoformat(retired_at)
        except ValueError:
            continue
        if state == "retired" or retired_date <= today:
            status = "retired"
        else:
            status = "deprecated"
        entry: dict = {
            "provider": "anthropic",
            "status": status,
            "retired_at": retired_at,
            "breaking_changes": [],
            "migrate_url": MIGRATE_URL,
            "source": "anthropic",
        }
        if status == "deprecated":
            entry["deprecated_at"] = retired_at
        models[model_id] = entry
    return models


def ensure_replacement_actives(models: dict[str, dict]) -> None:
    for repl in {e["replacement"] for e in models.values() if e.get("replacement")}:
        if repl not in models:
            models[repl] = {
                "provider": "anthropic",
                "status": "active",
                "replacement": None,
                "breaking_changes": [],
                "migrate_url": MIGRATE_URL,
                "source": "anthropic",
            }


def merge_status_replacements(status_models: dict[str, dict], history_models: dict[str, dict]) -> None:
    for model_id, entry in status_models.items():
        if entry.get("status") in {"deprecated", "retired"} and not entry.get("replacement"):
            hist = history_models.get(model_id)
            if hist and hist.get("replacement"):
                entry["replacement"] = hist["replacement"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Parse Anthropic deprecations into seed JSON")
    parser.add_argument("--input", type=Path, help="Local HTML/markdown file")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--today", default=date.today().isoformat())
    args = parser.parse_args()

    today = date.fromisoformat(args.today)
    page = args.input.read_text(encoding="utf-8") if args.input else fetch_page()

    history_md, aliases = parse_markdown_tables(page, today=today)
    history_html = parse_html_history(page, today=today)
    status_html = parse_html_status(page, today=today)

    models = {**history_md, **history_html, **status_html}
    merge_status_replacements(status_html, {**history_md, **history_html})

    ensure_replacement_actives(models)

    seed = {
        "sources": {
            "anthropic": {"url": ANTHROPIC_URL, "checked_at": today.isoformat()}
        },
        "aliases": aliases,
        "models": models,
    }
    print(f"Parsed {len(models)} models, {len(aliases)} aliases")

    if args.write:
        SEED_OUT.write_text(json.dumps(seed, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Wrote {SEED_OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
