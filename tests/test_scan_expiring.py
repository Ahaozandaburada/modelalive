from datetime import date

import pytest

from modelalive import check, list_expiring, scan_path
from modelalive.exceptions import ModelExpiringSoonError
from modelalive.scan import ScanReport


def test_list_expiring_includes_mythos():
    results = list_expiring(within_days=30, today=date(2026, 6, 28))
    ids = [r.model for r in results]
    assert "claude-mythos-preview" in ids


def test_warn_days_raises():
    with pytest.raises(ModelExpiringSoonError):
        check("claude-mythos-preview", warn_days=30, today=date(2026, 6, 28))


def test_scan_finds_retired_in_repo(tmp_path):
    sample = tmp_path / "app.py"
    sample.write_text('MODEL = "claude-sonnet-4-20250514"\n', encoding="utf-8")
    report = scan_path(tmp_path)
    assert isinstance(report, ScanReport)
    assert len(report.retired) == 1
    assert report.retired[0].model == "claude-sonnet-4-20250514"


def test_scan_clean_dir(tmp_path):
    sample = tmp_path / "app.py"
    sample.write_text('MODEL = "claude-sonnet-4-6"\n', encoding="utf-8")
    report = scan_path(tmp_path)
    assert report.findings == []
