#!/usr/bin/env python3
"""Copy canonical registry into the Python package bundle."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "registry" / "models.json"
TARGET = ROOT / "modelalive" / "data" / "models.json"
PROVIDERS_SRC = ROOT / "registry" / "providers.json"
PROVIDERS_DST = ROOT / "modelalive" / "data" / "providers.json"


def main() -> int:
    if not SOURCE.exists():
        print(f"Missing source registry: {SOURCE}", file=sys.stderr)
        return 1
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE, TARGET)
    print(f"Synced {SOURCE} -> {TARGET}")
    if PROVIDERS_SRC.exists():
        shutil.copy2(PROVIDERS_SRC, PROVIDERS_DST)
        print(f"Synced {PROVIDERS_SRC} -> {PROVIDERS_DST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
