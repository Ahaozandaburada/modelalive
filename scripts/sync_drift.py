#!/usr/bin/env python3
"""Sync registry from provider doc parsers + seed merge."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run(cmd: list[str]) -> int:
    print("+", " ".join(cmd))
    return subprocess.call(cmd, cwd=ROOT)


def main() -> int:
    steps = [
        [sys.executable, str(ROOT / "scripts" / "parse_openai_deprecations.py"), "--write"],
        [sys.executable, str(ROOT / "scripts" / "parse_together_deprecations.py"), "--write"],
        [sys.executable, str(ROOT / "scripts" / "parse_anthropic_deprecations.py"), "--write"],
        [sys.executable, str(ROOT / "scripts" / "parse_google_deprecations.py"), "--write"],
        [sys.executable, str(ROOT / "scripts" / "parse_fireworks_changelog.py"), "--write"],
        [sys.executable, str(ROOT / "scripts" / "parse_groq_deprecations.py"), "--write", "--offline"],
        [sys.executable, str(ROOT / "scripts" / "parse_mistral_deprecations.py"), "--write", "--offline"],
        [sys.executable, str(ROOT / "scripts" / "fetch_openrouter_models.py")],
        [sys.executable, str(ROOT / "scripts" / "generate_openrouter_crosswalk.py")],
        [sys.executable, str(ROOT / "scripts" / "merge_seeds.py")],
        [sys.executable, str(ROOT / "scripts" / "generate_host_seeds.py")],
        [sys.executable, str(ROOT / "scripts" / "merge_seeds.py")],
        [sys.executable, str(ROOT / "scripts" / "sync_registry.py")],
        [sys.executable, str(ROOT / "scripts" / "refresh_sources.py")],
        ["modelalive", "validate", "--strict"],
    ]
    for step in steps:
        code = run(step)
        if code != 0:
            return code
    print("Drift sync complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
