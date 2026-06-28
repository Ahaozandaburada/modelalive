"""Product quality: config env, scan patterns, API ensure semantics."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.main import app
from modelalive.scan import scan_path

ROOT = Path(__file__).resolve().parent.parent
CLI = [sys.executable, "-m", "modelalive.cli"]


def run_cli(*args: str, env: dict | None = None, cwd: Path | None = None):
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(
        [*CLI, *args],
        cwd=cwd or ROOT,
        capture_output=True,
        text=True,
        env=merged,
    )


def test_check_config_honors_modelalive_strict(tmp_path):
    config = tmp_path / "modelalive.toml"
    config.write_text('models = ["totally-unknown-model-xyz"]\n', encoding="utf-8")
    result = run_cli("check-config", "--file", str(config), env={"MODELALIVE_STRICT": "1"})
    assert result.returncode == 1


def test_check_config_toml_overrides_env(tmp_path):
    config = tmp_path / "modelalive.toml"
    config.write_text(
        'models = ["totally-unknown-model-xyz"]\n[ci]\nstrict_unknown = false\n',
        encoding="utf-8",
    )
    result = run_cli("check-config", "--file", str(config), env={"MODELALIVE_STRICT": "1"})
    assert result.returncode == 0


def test_check_env_strict_without_flag():
    result = run_cli("check", "totally-unknown-model-xyz", env={"MODELALIVE_STRICT": "1"})
    assert result.returncode == 1


def test_scan_openrouter_pattern(tmp_path):
    sample = tmp_path / "app.py"
    sample.write_text('MODEL = "anthropic/claude-sonnet-4-20250514"\n', encoding="utf-8")
    report = scan_path(tmp_path)
    assert any(f.model == "anthropic/claude-sonnet-4-20250514" for f in report.findings)


def test_scan_bedrock_pattern(tmp_path):
    sample = tmp_path / "app.py"
    sample.write_text('MODEL = "anthropic.claude-sonnet-4-20250514-v1:0"\n', encoding="utf-8")
    report = scan_path(tmp_path)
    assert any("claude-sonnet-4-20250514" in f.model for f in report.findings)


def test_scan_llama_pattern(tmp_path):
    sample = tmp_path / "app.py"
    sample.write_text('MODEL = "llama-3.3-70b-versatile"\n', encoding="utf-8")
    report = scan_path(tmp_path)
    assert report.findings == [] or all(f.status == "active" for f in report.findings)


def test_scan_deprecated_exits_nonzero(tmp_path):
    sample = tmp_path / "app.py"
    sample.write_text('MODEL = "claude-opus-4-1-20250805"\n', encoding="utf-8")
    result = run_cli("scan", str(tmp_path))
    assert result.returncode == 1


def test_ensure_unknown_strict_returns_404():
    client = TestClient(app)
    response = client.get(
        "/v1/ensure",
        params={"model": "totally-unknown-model-xyz", "strict_unknown": "true"},
    )
    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/problem+json")


def test_py_typed_marker_exists():
    assert (ROOT / "modelalive" / "py.typed").is_file()


def test_action_version_matches_package():
    action = (ROOT / "action.yml").read_text(encoding="utf-8")
    from modelalive import __version__

    block = action.split("version:")[1].split("warn-deprecated:")[0]
    assert f'default: "{__version__}"' in block
