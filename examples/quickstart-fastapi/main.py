"""Minimal FastAPI app — modelalive.ensure() before every LLM call."""

from __future__ import annotations

import os

import modelalive
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(
    title="Model Alive Quickstart",
    description="Pre-flight gate: retired model IDs are replaced before the API call.",
    version="1.0.0",
)


class ChatRequest(BaseModel):
    model: str = Field(examples=["claude-sonnet-4-6", "gpt-4o"])
    message: str = Field(min_length=1, max_length=4000)


class ChatResponse(BaseModel):
    queried_model: str
    safe_model: str
    reply: str
    lifecycle_status: str


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(body: ChatRequest) -> ChatResponse:
    """Run lifecycle gate, then call OpenAI-compatible API (or mock)."""
    try:
        result = modelalive.alive(body.model)
        safe_model = modelalive.ensure(body.model)
    except modelalive.ModelRetiredError as exc:
        raise HTTPException(status_code=410, detail=str(exc)) from exc
    except modelalive.ModelUnknownError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    reply = _complete(safe_model, body.message)
    return ChatResponse(
        queried_model=body.model,
        safe_model=safe_model,
        reply=reply,
        lifecycle_status=result.status,
    )


def _complete(model: str, message: str) -> str:
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        return f"[mock] model={model!r} message={message[:80]!r}"

    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": message}],
        max_tokens=256,
    )
    return response.choices[0].message.content or ""
