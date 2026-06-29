"""HTTP probe tests with mocked clients."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from modelalive.probe import _probe_once, probe_responses, resolve_probe_backend


def test_resolve_openrouter():
    assert resolve_probe_backend("openai/gpt-4o") == "openrouter"


def test_resolve_bedrock_model_id():
    assert resolve_probe_backend("anthropic.claude-sonnet-4-6-v1:0") == "bedrock"


def test_probe_once_openai():
    client = MagicMock()
    client.post.return_value.json.return_value = {
        "choices": [{"message": {"content": "hello"}}]
    }
    client.post.return_value.raise_for_status = MagicMock()
    text = _probe_once(
        client,
        backend="openai",
        base="https://api.openai.com/v1",
        key="sk-test",
        model="gpt-4o",
        message="hi",
        temperature=0.0,
        max_tokens=16,
    )
    assert text == "hello"


def test_probe_once_anthropic():
    client = MagicMock()
    client.post.return_value.json.return_value = {
        "content": [{"type": "text", "text": "anthropic reply"}]
    }
    client.post.return_value.raise_for_status = MagicMock()
    text = _probe_once(
        client,
        backend="anthropic",
        base="https://api.anthropic.com/v1",
        key="sk-ant",
        model="claude-sonnet-4-6",
        message="hi",
        temperature=0.0,
        max_tokens=16,
    )
    assert text == "anthropic reply"


@patch("modelalive.probe.list_stable_prompts")
@patch("httpx.Client")
def test_probe_responses_openai(mock_client_cls, mock_prompts):
    mock_prompts.return_value = [{"id": "json_echo", "message": "test"}]
    mock_client = MagicMock()
    mock_client_cls.return_value.__enter__.return_value = mock_client
    mock_client.post.return_value.json.return_value = {
        "choices": [{"message": {"content": "ok"}}]
    }
    mock_client.post.return_value.raise_for_status = MagicMock()

    with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test"}, clear=False):
        out = probe_responses("gpt-4o", samples=1)
    assert out["json_echo"] == ["ok"]


def test_probe_bedrock_requires_boto3(monkeypatch):
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    import builtins
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "boto3":
            raise ImportError("no boto3")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    from modelalive.probe import _probe_bedrock

    with pytest.raises(RuntimeError, match="boto3"):
        _probe_bedrock("anthropic.claude-3-haiku", "hi", region="us-east-1", temperature=0, max_tokens=8)
