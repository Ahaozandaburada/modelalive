"""Doc parser smoke tests."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_together_parsed_seed_exists():
    path = ROOT / "registry" / "seeds" / "together_parsed.json"
    assert path.exists()
    seed = json.loads(path.read_text())
    assert len(seed["models"]) >= 150


def test_anthropic_parsed_seed_exists():
    path = ROOT / "registry" / "seeds" / "anthropic_parsed.json"
    assert path.exists()
    seed = json.loads(path.read_text())
    assert len(seed["models"]) >= 10
    assert "claude-sonnet-4-20250514" in seed["models"]
