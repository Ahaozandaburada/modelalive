#!/usr/bin/env python3
"""Generate OpenRouter slug → canonical model aliases."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "registry" / "seeds" / "openrouter.json"

# OpenRouter slug -> canonical registry model ID
CROSSWALK: dict[str, str] = {
    # OpenAI
    "openai/gpt-4o": "gpt-4o",
    "openai/gpt-4o-mini": "gpt-4o-mini",
    "openai/gpt-4-turbo": "gpt-4-turbo-2024-04-09",
    "openai/gpt-5.5": "gpt-5.5",
    "openai/gpt-5.4-mini": "gpt-5.4-mini",
    "openai/o3": "o3",
    "openai/o4-mini": "o4-mini",
    "openai/o1": "o1",
    # Anthropic
    "anthropic/claude-sonnet-4-6": "claude-sonnet-4-6",
    "anthropic/claude-opus-4-8": "claude-opus-4-8",
    "anthropic/claude-3-5-sonnet-20241022": "claude-3-5-sonnet-20241022",
    "anthropic/claude-3-5-haiku-20241022": "claude-3-5-haiku-20241022",
    "anthropic/claude-3-opus-20240229": "claude-3-opus-20240229",
    "anthropic/claude-sonnet-4-20250514": "claude-sonnet-4-20250514",
    # Google
    "google/gemini-2.5-flash": "gemini-2.5-flash",
    "google/gemini-3.5-flash": "gemini-3.5-flash",
    "google/gemini-2.0-flash": "gemini-2.0-flash",
    "google/gemini-2.5-pro": "gemini-2.5-pro",
    # xAI
    "x-ai/grok-4.3": "grok-4.3",
    "x-ai/grok-3": "grok-3",
    "x-ai/grok-2-latest": "grok-2-latest",
    # Mistral
    "mistralai/mistral-large-2411": "mistral-large-2411",
    "mistralai/mistral-small-2506": "mistral-small-2506",
    "mistralai/mixtral-8x7b-instruct-v0.1": "mixtral-8x7b-32768",
    # DeepSeek
    "deepseek/deepseek-chat": "deepseek-chat",
    "deepseek/deepseek-reasoner": "deepseek-reasoner",
    "deepseek/deepseek-r1": "deepseek-r1",
    "deepseek/deepseek-v3.2": "deepseek-chat",
    "deepseek/deepseek-v3.1-terminus": "deepseek-chat",
    "deepseek/deepseek-v4-pro": "deepseek-v4-pro",
    "deepseek/deepseek-v4-flash": "deepseek-v4-flash",
    "deepseek/deepseek-r1-distill-llama-70b": "meta-llama/Llama-3.3-70B-Instruct",
    # Qwen
    "qwen/qwen3.7-max": "qwen3.7-max",
    "qwen/qwen3.7-plus": "qwen3.7-plus",
    "qwen/qwen3.6-plus": "qwen3.6-plus",
    "qwen/qwen3.6-flash": "qwen3.6-flash",
    "qwen/qwen3.5-plus": "qwen3.5-plus",
    "qwen/qwen3.5-flash": "qwen3.5-flash",
    "qwen/qwen3-coder-plus": "qwen3-coder-plus",
    "qwen/qwen3-max": "qwen3-max",
    "qwen/qwen3-coder": "qwen3-coder-plus",
    "qwen/qwen-2.5-coder-32b-instruct": "qwen2.5-coder-32b-instruct",
    "qwen/qwen2.5-vl-72b-instruct": "qwen2.5-72b-instruct",
    "qwen/qwen3.5-397b-a17b": "Qwen/Qwen3.5-397B-A17B",
    "qwen/qwen3-235b-a22b-instruct-2507": "qwen3.7-plus",
    # Meta Llama
    "meta-llama/llama-3.3-70b-instruct": "meta-llama/Llama-3.3-70B-Instruct",
    "meta-llama/llama-3.1-8b-instruct": "meta-llama/Meta-Llama-3.1-8B-Instruct",
    "meta-llama/llama-3.1-70b-instruct": "meta-llama/Meta-Llama-3.1-70B-Instruct",
    "meta-llama/llama-3.2-3b-instruct": "meta-llama/Llama-3.2-3B-Instruct",
    "meta-llama/llama-3.2-11b-vision-instruct": "meta-llama/Llama-3.2-11B-Vision-Instruct",
    "meta-llama/llama-3.2-90b-vision-instruct": "meta-llama/Llama-3.2-90B-Vision-Instruct",
    "meta-llama/llama-3.2-1b-instruct": "meta-llama/Llama-3.2-1B-Instruct",
    "meta-llama/llama-2-13b-chat-hf": "meta-llama/Llama-2-13b-chat-hf",
    # Cohere
    "cohere/command-r-plus": "command-r-plus-08-2024",
    "cohere/command-r7b-12-2024": "command-r7b-12-2024",
    "cohere/command-a-03-2025": "command-a-03-2025",
    # Perplexity
    "perplexity/sonar": "sonar",
    "perplexity/sonar-pro": "sonar-pro",
    "perplexity/sonar-reasoning": "sonar-reasoning",
    # Groq (OpenRouter routes)
    "groq/llama-3.3-70b-versatile": "llama-3.3-70b-versatile",
    "groq/llama3-70b-8192": "llama3-70b-8192",
    # Together paths on OpenRouter
    "together/meta-llama/llama-3.3-70b-instruct-turbo": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
    # NVIDIA
    "nvidia/llama-3.3-nemotron-super-49b-v1.5": "nvidia/llama-3.3-nemotron-super-49b-v1.5",
    # AI21
    "ai21/jamba-1.5-large": "jamba-1.5-large",
    "ai21/jamba-1.5-mini": "jamba-1.5-mini",
}


def main() -> int:
    seed = {
        "sources": {
            "openrouter": {
                "url": "https://openrouter.ai/docs/guides/overview/models",
                "checked_at": "2026-06-28",
            }
        },
        "aliases": CROSSWALK,
        "models": {},
    }
    OUT.write_text(json.dumps(seed, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(CROSSWALK)} OpenRouter aliases -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
