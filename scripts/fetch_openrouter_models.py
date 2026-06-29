#!/usr/bin/env python3
"""Fetch OpenRouter model catalog and merge into registry seeds."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "registry" / "seeds" / "openrouter.json"
REGISTRY = ROOT / "registry" / "models.json"


def fetch_models() -> list[dict]:
    try:
        import httpx
    except ImportError as exc:
        raise SystemExit("Install httpx: pip install modelalive[http]") from exc

    response = httpx.get("https://openrouter.ai/api/v1/models", timeout=60.0, follow_redirects=True)
    response.raise_for_status()
    return list(response.json().get("data") or [])


def canonical_for_slug(slug: str, known_models: dict[str, object]) -> str | None:
    def usable(key: str) -> bool:
        entry = known_models.get(key)
        if not isinstance(entry, dict):
            return key in known_models
        if entry.get("provider") == "openrouter":
            return False
        return True

    if usable(slug):
        return slug
    lower_index = {k.lower(): k for k, v in known_models.items() if usable(k)}
    if slug.lower() in lower_index:
        return lower_index[slug.lower()]
    if "/" in slug:
        tail = slug.split("/")[-1]
        if usable(tail):
            return tail
        if tail.lower() in lower_index:
            return lower_index[tail.lower()]
    return None


def build_seed(*, dry_run: bool = False) -> dict:
    today = date.today().isoformat()
    known_models: dict[str, object] = {}
    if REGISTRY.exists():
        known_models = json.loads(REGISTRY.read_text(encoding="utf-8")).get("models", {})

    # Hand-curated crosswalk (fallback when live fetch fails)
    crosswalk_path = ROOT / "scripts" / "generate_openrouter_crosswalk.py"
    crosswalk: dict[str, str] = {}
    if crosswalk_path.exists():
        import importlib.util

        spec = importlib.util.spec_from_file_location("openrouter_crosswalk", crosswalk_path)
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            crosswalk = dict(getattr(mod, "CROSSWALK", {}) or {})

    aliases = dict(crosswalk)
    models: dict[str, dict] = {}
    fetched = 0
    mapped = 0

    try:
        catalog = fetch_models()
    except Exception as exc:  # noqa: BLE001
        print(f"OpenRouter fetch failed ({exc}); using static crosswalk only.", file=sys.stderr)
        catalog = []

    for row in catalog:
        slug = str(row.get("id") or "").strip()
        if not slug:
            continue
        fetched += 1
        if slug in aliases:
            continue
        canonical = canonical_for_slug(slug, known_models)
        if canonical and canonical != slug:
            aliases[slug] = canonical
            mapped += 1
        elif slug not in models:
            # Only register unmapped OpenRouter routes (avoid shadowing canonical aliases)
            models[slug] = {
                "provider": "openrouter",
                "status": "active",
                "replacement": None,
                "breaking_changes": [],
                "migrate_url": "https://openrouter.ai/models",
                "source": "openrouter",
                "notes": "OpenRouter route; unmapped to canonical",
            }

    seed = {
        "sources": {
            "openrouter": {
                "url": "https://openrouter.ai/api/v1/models",
                "checked_at": today,
            }
        },
        "aliases": aliases,
        "models": models,
    }
    print(f"OpenRouter: fetched={fetched} mapped={mapped} aliases={len(aliases)} routes={len(models)}")
    if not dry_run:
        OUT.write_text(json.dumps(seed, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Wrote {OUT}")
    return seed


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync OpenRouter catalog into registry seed")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    build_seed(dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
