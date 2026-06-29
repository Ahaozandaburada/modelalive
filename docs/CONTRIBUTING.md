# Contributing to Model Alive

Thank you for helping make Model Alive the universal LLM lifecycle registry.

## Adding or updating models

1. **Find the provider seed** under `registry/seeds/{provider}.json`
2. Add the model with required fields:

```json
"model-id-here": {
  "provider": "openai",
  "status": "active",
  "replacement": null,
  "breaking_changes": [],
  "migrate_url": "https://official-docs-url",
  "source": "openai"
}
```

For `deprecated` or `retired` models, include `replacement`, and date fields:

```json
"old-model": {
  "provider": "anthropic",
  "status": "retired",
  "retired_at": "2026-06-15",
  "replacement": "claude-sonnet-4-6",
  "breaking_changes": [],
  "migrate_url": "https://platform.claude.com/docs/en/about-claude/model-deprecations",
  "source": "anthropic"
}
```

3. **Aliases** go in the seed's `aliases` object — never self-referencing (`a → a`).
4. Run locally:

```bash
python scripts/merge_seeds.py
python scripts/sync_registry.py
modelalive validate --strict
pytest -q
```

5. Open a PR using the registry template.

## Provider doc parsers

Automated parsers live in `scripts/`:

| Script | Source |
|--------|--------|
| `parse_openai_deprecations.py` | OpenAI deprecations page |
| `parse_anthropic_deprecations.py` | Anthropic model deprecations |
| `parse_together_deprecations.py` | Together AI deprecations |
| `generate_openrouter_crosswalk.py` | OpenRouter slug → canonical |

Run full drift sync:

```bash
python scripts/sync_drift.py
```

Parsed output goes to `*_parsed.json` seeds; manual seeds always win on conflicts.

## OpenRouter slugs

Add new slugs to `scripts/generate_openrouter_crosswalk.py` `CROSSWALK` dict, then:

```bash
python scripts/generate_openrouter_crosswalk.py
python scripts/merge_seeds.py
```

## Tests

Every behavior change needs a test. Registry additions should include at least one `tests/test_universal.py` or provider-specific case.

## Accuracy policy

See [ACCURACY.md](ACCURACY.md). Always link to an official provider source URL with `checked_at` date.

## Adoption & launch

- **Examples:** [examples/README.md](../examples/README.md) — FastAPI quickstart, Stable CI, GitHub Actions
- **Marketing copy:** [docs/marketing/](../marketing/) — Show HN, Reddit, X thread (copy-paste)
- **Terminal demo:** `bash scripts/record_demo.sh` or `bash scripts/record_demo.sh --cast`
- **Design partners:** [marketing/design-partner.md](../marketing/design-partner.md)

## Issue templates

| Template | Use |
|----------|-----|
| [add-model.yml](../../.github/ISSUE_TEMPLATE/add-model.yml) | New model or status fix |
| [provider-request.yml](../../.github/ISSUE_TEMPLATE/provider-request.yml) | New provider/host |
| [false-positive.yml](../../.github/ISSUE_TEMPLATE/false-positive.yml) | Wrong lifecycle data |
| [design-partner.yml](../../.github/ISSUE_TEMPLATE/design-partner.yml) | Integration feedback |
