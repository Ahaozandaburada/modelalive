"""Integration: wrap OpenAI client calls with modelalive.ensure()."""

from __future__ import annotations

import modelalive


def chat(model: str, messages: list[dict], client) -> str:
    safe_model = modelalive.ensure(model)
    response = client.chat.completions.create(model=safe_model, messages=messages)
    return response.choices[0].message.content or ""
