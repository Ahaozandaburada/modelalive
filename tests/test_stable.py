"""Behavioral stability (ghost drift) tests — no live API calls."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from modelalive.exceptions import StableShiftError
from modelalive.stable import (
    Fingerprint,
    PromptFingerprint,
    assert_stable,
    compare_fingerprints,
    fingerprint_from_responses,
    list_stable_prompts,
    response_distance,
)


def test_stable_prompts_loaded():
    prompts = list_stable_prompts()
    assert len(prompts) >= 5
    assert prompts[0]["id"]


def test_identical_responses_zero_distance():
    text = '{"ok": true, "n": 42}'
    assert response_distance(text, text) == 0.0


def test_different_responses_positive_distance():
    assert response_distance("hello world", "completely different output") > 0.2


def test_fingerprint_roundtrip(tmp_path: Path):
    fp = fingerprint_from_responses(
        "gpt-4o",
        {
            "json_echo": ['{"ok": true, "n": 42}'],
            "math_fixed": ["391"],
            "refusal_probe": ["I can't help with that."],
            "code_snippet": ["def is_palindrome(s):\n    return s == s[::-1]"],
            "style_haiku": ["Rain on the roof\nMetal sings in steady rhythm\nNight keeps its own time"],
        },
    )
    path = tmp_path / "fp.json"
    fp.save(path)
    loaded = Fingerprint.load(path)
    assert loaded.model == "gpt-4o"
    assert len(loaded.prompts) == 5


def test_compare_stable_baseline():
    responses = {
        "json_echo": ['{"ok": true, "n": 42}'],
        "math_fixed": ["391"],
        "refusal_probe": ["Sorry, I can't assist."],
        "code_snippet": ["def is_palindrome(s):\n    return s == s[::-1]"],
        "style_haiku": ["Soft rain on tin\nEchoes through the empty night\nSilver rhythm falls"],
    }
    baseline = fingerprint_from_responses("gpt-4o", responses)
    current = fingerprint_from_responses("gpt-4o", responses)
    report = compare_fingerprints(baseline, current, threshold=0.25)
    assert report.stable is True
    assert report.mean_distance == 0.0


def test_compare_detects_drift():
    base = {
        "json_echo": ['{"ok": true, "n": 42}'],
        "math_fixed": ["391"],
        "refusal_probe": ["I cannot provide lock picking instructions."],
        "code_snippet": ["def is_palindrome(s):\n    return s == s[::-1]"],
        "style_haiku": ["Line one\nLine two\nLine three"],
    }
    shifted = dict(base)
    shifted["math_fixed"] = ["999"]
    shifted["code_snippet"] = ["def add(a,b): return a+b"]
    baseline = fingerprint_from_responses("gpt-4o", base)
    current = fingerprint_from_responses("gpt-4o", shifted)
    report = compare_fingerprints(baseline, current, threshold=0.25)
    assert report.stable is False
    assert report.prompt_shifts


def test_assert_stable_raises():
    baseline = fingerprint_from_responses("m", {"json_echo": ["A"], "math_fixed": ["1"], "refusal_probe": ["no"], "code_snippet": ["x"], "style_haiku": ["h"]})
    current = fingerprint_from_responses("m", {"json_echo": ["Z"], "math_fixed": ["9"], "refusal_probe": ["yes"], "code_snippet": ["y"], "style_haiku": ["k"]})
    with pytest.raises(StableShiftError):
        assert_stable(baseline, current, threshold=0.01)


def test_cli_stable_diff(tmp_path: Path):
    from modelalive.cli import main
    import io
    import contextlib

    base = fingerprint_from_responses(
        "gpt-4o",
        {p["id"]: ["same"] for p in list_stable_prompts()},
    )
    cur = fingerprint_from_responses(
        "gpt-4o",
        {p["id"]: ["same"] for p in list_stable_prompts()},
    )
    b = tmp_path / "b.json"
    c = tmp_path / "c.json"
    base.save(b)
    cur.save(c)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = main(["stable", "diff", str(b), str(c), "--json"])
    assert code == 0
    data = json.loads(buf.getvalue())
    assert data["stable"] is True
