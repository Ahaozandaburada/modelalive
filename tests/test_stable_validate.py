from modelalive.stable import fingerprint_from_responses, list_stable_prompts, validate_fingerprint


def test_validate_fingerprint_ok():
    fp = fingerprint_from_responses("gpt-4o", {p["id"]: ["x"] for p in list_stable_prompts()})
    assert validate_fingerprint(fp.to_dict()) == []


def test_validate_fingerprint_bad_kind():
    assert "kind" in validate_fingerprint({"model": "x", "prompts": []})[0]
