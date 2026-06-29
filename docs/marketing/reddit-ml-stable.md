# Reddit — r/MachineLearning (or r/artificial)

**Flair:** Resource / Project  
**Note:** Read sub rules — some require `[P]` prefix in title.

---

## Title

[P] Model Alive — detect retired LLM model IDs and silent endpoint drift (Stable layer)

---

## Body

**Problem:** Production apps hardcode model IDs. Providers retire them on schedule; sometimes the **same ID** changes behavior underneath (routing, quantization, weights) without a version bump — uptime stays green.

**Model Alive** is an open-source pre-flight gate:

1. **Alive** — registry synced from official deprecation pages (Anthropic, OpenAI, Google, Groq, Together, Bedrock, Azure, OpenRouter live sync). Answers: is this ID retired? what's the replacement?

2. **Stable** — inspired by Stability Monitor (arxiv:2603.19022). Five fixed prompts, fingerprint comparison. Catches ghost drift under the same model name in CI.

```bash
pip install modelalive
modelalive check gemini-2.0-flash          # retired → gemini-3.5-flash
modelalive stable baseline gpt-4o -o baseline.json
modelalive stable check gpt-4o -b baseline.json
```

Python + TypeScript + Go SDKs, GitHub Action, hosted API.

Links:
- https://github.com/Ahaozandaburada/modelalive
- https://pypi.org/project/modelalive/
- Stable docs: https://github.com/Ahaozandaburada/modelalive/blob/main/docs/STABLE.md

**Limits (stated upfront):** Registry lag; unknown models pass by default; Stable uses a lightweight 5-prompt metric — not a full research-grade monitor.

Looking for design partners to harden provider coverage. Issues welcome.
