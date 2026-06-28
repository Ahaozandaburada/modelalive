#!/usr/bin/env python3
"""Merge registry/seeds/*.json into registry/models.json."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "registry" / "models.json"
BUNDLE = ROOT / "modelalive" / "data" / "models.json"
SEEDS_DIR = ROOT / "registry" / "seeds"


def main() -> int:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    models = registry.setdefault("models", {})
    aliases: dict[str, str] = {}
    sources = registry.setdefault("sources", {})
    added = 0

    SKIP_PARSED = {
        "openai_parsed.json",
        "together_parsed.json",
        "anthropic_parsed.json",
        "google_parsed.json",
        "fireworks_parsed.json",
    }

    for seed_file in sorted(SEEDS_DIR.glob("*.json")):
        seed = json.loads(seed_file.read_text(encoding="utf-8"))
        for key, meta in seed.get("sources", {}).items():
            sources[key] = meta
        for model_id, entry in seed.get("models", {}).items():
            if seed_file.name in SKIP_PARSED and model_id in models:
                continue  # manual seed wins over parsed drift
            if model_id not in models:
                models[model_id] = entry
                added += 1
            else:
                models[model_id].update(entry)
        for alias, target in seed.get("aliases", {}).items():
            if alias == target:
                continue
            if target in aliases and target not in models:
                continue
            aliases[alias] = target

    registry["aliases"] = aliases

    REGISTRY.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    BUNDLE.write_text(REGISTRY.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"Merged seeds — {added} new models, {len(models)} total")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
