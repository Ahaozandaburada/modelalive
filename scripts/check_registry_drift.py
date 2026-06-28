#!/usr/bin/env python3
"""Fail CI if committed registry is stale vs provider doc parsers."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

TRACKED = [
    "registry/models.json",
    "modelalive/data/models.json",
    "registry/seeds/bedrock.json",
    "registry/seeds/azure.json",
]


def run(cmd: list[str], *, cwd: Path) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=cwd, check=True)


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp) / "modelalive"
        shutil.copytree(ROOT, work, ignore=shutil.ignore_patterns(".git", ".venv", "node_modules", "dist", "__pycache__"))
        run([sys.executable, "scripts/sync_drift.py"], cwd=work)
        diffs: list[str] = []
        for rel in TRACKED:
            committed = ROOT / rel
            synced = work / rel
            if not committed.exists() or not synced.exists():
                continue
            if committed.read_bytes() != synced.read_bytes():
                diffs.append(rel)
        if diffs:
            print("Registry drift detected — re-run scripts/sync_drift.py and commit:")
            for path in diffs:
                print(f"  - {path}")
            return 1
    print("Registry matches provider doc parsers.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
