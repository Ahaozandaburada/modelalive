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
    aliases = registry.setdefault("aliases", {})
    added = 0

    for seed_file in sorted(SEEDS_DIR.glob("*.json")):
        seed = json.loads(seed_file.read_text(encoding="utf-8"))
        for model_id, entry in seed.get("models", {}).items():
            if model_id not in models:
                models[model_id] = entry
                added += 1
            else:
                models[model_id].update(entry)
        for alias, target in seed.get("aliases", {}).items():
            aliases[alias] = target

    REGISTRY.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    BUNDLE.write_text(REGISTRY.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"Merged seeds — {added} new models, {len(models)} total")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
