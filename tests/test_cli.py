"""CLI integration tests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLI = [sys.executable, "-m", "modelalive.cli"]


def run_cli(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [*CLI, *args],
        cwd=cwd or ROOT,
        capture_output=True,
        text=True,
    )


def test_check_retired_exits_1():
    result = run_cli("check", "claude-sonnet-4-20250514")
    assert result.returncode == 1
    assert "DEAD" in result.stdout or "retired" in result.stdout.lower()


def test_check_active_exits_0():
    result = run_cli("check", "claude-sonnet-4-6")
    assert result.returncode == 0
    assert "ALIVE" in result.stdout


def test_check_json_output():
    result = run_cli("check", "--json", "gpt-5.5")
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data[0]["status"] == "active"


def test_ensure_prints_safe_model():
    result = run_cli("ensure", "gemini-2.0-flash")
    assert result.returncode == 0
    assert result.stdout.strip() == "gemini-3.5-flash"


def test_resolve_output():
    result = run_cli("resolve", "claude-sonnet-4-20250514")
    assert result.returncode == 0
    assert result.stdout.strip() == "claude-sonnet-4-6"


def test_info_json():
    result = run_cli("info", "claude-sonnet-4-6")
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["provider"] == "anthropic"


def test_list_retired_openai():
    result = run_cli("list", "--status", "retired", "--provider", "openai")
    assert result.returncode == 0
    assert "gpt-4-0314" in result.stdout


def test_validate_strict():
    result = run_cli("validate", "--strict")
    assert result.returncode == 0
    assert "Registry OK" in result.stdout


def test_expiring_json():
    result = run_cli("expiring", "--days", "30", "--json")
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert isinstance(data, list)


def test_scan_finds_retired(tmp_path):
    sample = tmp_path / "app.py"
    sample.write_text('MODEL = "claude-sonnet-4-20250514"\n', encoding="utf-8")
    result = run_cli("scan", str(tmp_path))
    assert result.returncode == 1
    assert "claude-sonnet-4-20250514" in result.stdout


def test_scan_clean(tmp_path):
    sample = tmp_path / "app.py"
    sample.write_text('MODEL = "claude-sonnet-4-6"\n', encoding="utf-8")
    result = run_cli("scan", str(tmp_path))
    assert result.returncode == 0


def test_check_config_project_file():
    result = run_cli("check-config")
    assert result.returncode == 0


def test_cli_providers():
    result = run_cli("providers")
    assert result.returncode == 0
    assert "xai" in result.stdout
    assert "together" in result.stdout


def test_bedrock_alias_via_cli():
    result = run_cli("resolve", "anthropic.claude-sonnet-4-6-v1:0")
    assert result.returncode == 0
    assert result.stdout.strip() == "claude-sonnet-4-6"


def test_strict_unknown_fails():
    result = run_cli("check", "--strict-unknown", "unknown-model-xyz-abc")
    assert result.returncode == 1


def test_list_json_output():
    result = run_cli("list", "--status", "active", "--provider", "qwen", "--json")
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert "models" in data
    assert "qwen3.7-max" in data["models"]


def test_providers_json():
    result = run_cli("providers", "--json")
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert "qwen" in data["providers"]


def test_check_multiple_models():
    result = run_cli("check", "gpt-4o", "claude-sonnet-4-6")
    assert result.returncode == 0


def test_qwen_openrouter_via_cli():
    result = run_cli("resolve", "qwen/qwen3.7-max")
    assert result.returncode == 0
    assert result.stdout.strip() == "qwen3.7-max"
