#!/usr/bin/env python3
"""Copy canonical registry into the Python package bundle."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "registry" / "models.json"
TARGET = ROOT / "modelalive" / "data" / "models.json"
GO_TARGET = ROOT / "go" / "modelalive" / "registry.json"
PROVIDERS_SRC = ROOT / "registry" / "providers.json"
PROVIDERS_DST = ROOT / "modelalive" / "data" / "providers.json"
STABLE_SRC = ROOT / "modelalive" / "data" / "stable_prompts.json"
JS_STABLE = ROOT / "js" / "stable_prompts.json"
GO_STABLE = ROOT / "go" / "modelalive" / "stable_prompts.json"


def main() -> int:
    if not SOURCE.exists():
        print(f"Missing source registry: {SOURCE}", file=sys.stderr)
        return 1
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE, TARGET)
    print(f"Synced {SOURCE} -> {TARGET}")
    GO_TARGET.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE, GO_TARGET)
    print(f"Synced {SOURCE} -> {GO_TARGET}")
    if PROVIDERS_SRC.exists():
        shutil.copy2(PROVIDERS_SRC, PROVIDERS_DST)
        print(f"Synced {PROVIDERS_SRC} -> {PROVIDERS_DST}")
    if STABLE_SRC.exists():
        for target in (JS_STABLE, GO_STABLE):
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(STABLE_SRC, target)
            print(f"Synced {STABLE_SRC} -> {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
