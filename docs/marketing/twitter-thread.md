# X / LinkedIn thread — copy-paste

Post as a thread (X) or single LinkedIn post with line breaks.

---

## Post 1

Your LLM app probably still calls `gemini-2.0-flash`.

Google retired it June 1. The API might already 404 — or worse, route somewhere else under the same string.

One command:

```
pip install modelalive
modelalive check gemini-2.0-flash
```

---

## Post 2

Model Alive = pre-flight gate before every inference call.

Alive → is this model ID officially dead?  
Stable → same ID, different behavior? (ghost drift)

765 models · OpenRouter · Ollama · Bedrock · Azure

---

## Post 3

CI in 3 lines:

```yaml
- uses: Ahaozandaburada/modelalive@v1.6.0
  with:
    models: claude-sonnet-4-6
    strict-unknown: "true"
```

Open source: https://github.com/Ahaozandaburada/modelalive

---

## Post 4 (optional CTA)

We shipped v1.6 yesterday — zero adoption so far, honest feedback wanted.

Missing your provider? Open an issue, we'll add it:  
https://github.com/Ahaozandaburada/modelalive/issues/new?template=add-model.yml
