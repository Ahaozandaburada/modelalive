"""LangChain: validate model before ChatOpenAI / ChatAnthropic invocation."""

from __future__ import annotations

import modelalive


def safe_model(model: str) -> str:
    return modelalive.ensure(model)


# Usage:
# from langchain_openai import ChatOpenAI
# llm = ChatOpenAI(model=safe_model("claude-sonnet-4-20250514"))

if __name__ == "__main__":
    for mid in ["claude-sonnet-4-20250514", "gemini-2.0-flash", "gpt-5.5"]:
        print(mid, "→", safe_model(mid))
