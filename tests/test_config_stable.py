"""Config + stable integration tests."""

from __future__ import annotations

from pathlib import Path

from modelalive.config_file import load_config
from modelalive.cli import main


def test_load_config_with_stable(tmp_path: Path):
    cfg = tmp_path / "modelalive.toml"
    cfg.write_text(
        """
models = ["gpt-4o"]
[[stable]]
model = "gpt-4o"
baseline = "examples/baselines/gpt-4o.json"
threshold = 0.25
""",
        encoding="utf-8",
    )
    loaded = load_config(cfg)
    assert loaded.models == ["gpt-4o"]
    assert len(loaded.stable) == 1
    assert loaded.stable[0].model == "gpt-4o"


def test_check_config_offline_stable(monkeypatch):
    monkeypatch.setenv("MODELALIVE_STABLE_SKIP_PROBE", "1")
    assert main(["check-config", "--file", "examples/modelalive.toml"]) == 0


def test_stable_validate_example_baseline():
    assert main(["stable", "validate", "examples/baselines/gpt-4o.json"]) == 0
