"""CLI check-config command tests."""

from pathlib import Path

import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent


def test_check_config_default_file():
    result = subprocess.run(
        [sys.executable, "-m", "modelalive.cli", "check-config"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


def test_check_config_custom_file(tmp_path):
    path = tmp_path / "modelalive.toml"
    path.write_text('models = ["claude-sonnet-4-6"]\n', encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-m", "modelalive.cli", "check-config", "--file", str(path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
