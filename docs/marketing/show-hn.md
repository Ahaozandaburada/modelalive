# Show HN — copy-paste draft

**When:** Tuesday or Wednesday, 09:00–11:00 US Pacific  
**URL:** https://news.ycombinator.com/submit

---

## Title (pick one)

1. **Show HN: Model Alive – pre-flight check before every LLM API call**
2. Show HN: Catch retired model IDs and ghost drift before production breaks
3. Show HN: modelalive – `pip install` gate for LLM lifecycle + behavioral drift

---

## Body

Hardcoded model IDs break silently. Google retires Gemini 2.0 Flash, Anthropic sunsets Sonnet 4 — your app keeps calling the old string until users see errors.

**Model Alive** is a pre-flight gate you run before every inference call:

```bash
pip install modelalive
modelalive check claude-sonnet-4-20250514   # exit 1 — retired
modelalive ensure claude-sonnet-4-20250514  # → claude-sonnet-4-6
```

Two layers:

| Layer | Question |
|-------|----------|
| **Alive** | Is this model ID officially retired/deprecated? (765 models, 22 providers, offline registry) |
| **Stable** | Same ID, different behavior? (5-prompt fingerprint for ghost drift) |

Works with OpenRouter, Ollama, Bedrock, Azure paths — one normalization pipeline.

- **PyPI:** https://pypi.org/project/modelalive/
- **npm:** https://www.npmjs.com/package/modelalive
- **Hosted API:** https://modelalive.fly.dev/status
- **Repo:** https://github.com/Ahaozandaburada/modelalive
- **FastAPI quickstart:** https://github.com/Ahaozandaburada/modelalive/tree/main/examples/quickstart-fastapi

GitHub Action (3 lines in CI):

```yaml
- uses: Ahaozandaburada/modelalive@v1.6.1
  with:
    models: claude-sonnet-4-6 gpt-4o
    strict-unknown: "true"
```

**Honest limits:** Registry can lag providers by days; unknown models pass by default unless `--strict-unknown`. Stable is not a full Stability Monitor replacement — it's a lightweight CI probe.

Shipped v1.6.1 yesterday. Feedback welcome — especially missing providers or false positives.

---

## First comment (post immediately after submit)

Author here. Quick links:

- Stable (ghost drift): https://github.com/Ahaozandaburada/modelalive/blob/main/docs/STABLE.md
- Universal IDs (Ollama/OpenRouter): https://github.com/Ahaozandaburada/modelalive/blob/main/docs/UNIVERSAL.md
- Add a model: https://github.com/Ahaozandaburada/modelalive/issues/new?template=add-model.yml

Happy to add your provider to the registry if you open an issue.
