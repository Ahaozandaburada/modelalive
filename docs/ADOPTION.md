# Adoption guide — agents, CI, and teams

Make every LLM integration verify model IDs **before** production breaks — lifecycle (**Alive**) and behavioral drift (**Stable**).

| Audience | Start here |
|----------|------------|
| **Cursor / Copilot agents** | [Cursor rule](#cursor-rule) + [Agent skill](#agent-skill) |
| **GitHub Actions** | [Workflow examples](#github-actions-copy-paste) — lifecycle + optional `stable-baseline` |
| **Local dev** | [Pre-commit](#pre-commit) + `modelalive.toml` |
| **Any agent framework** | [AGENTS.md snippet](#agentsmd-for-any-repo) |
| **Launch / distribution** | [Marketing copy](marketing/README.md) — Show HN, Reddit, X |
| **Runnable demo** | [examples/quickstart-fastapi/](../examples/quickstart-fastapi/) |

Install once:

```bash
pip install modelalive    # Python CLI + SDK
npm install modelalive    # TypeScript
```

---

## Cursor rule

Copy into **your app repo** (not only this monorepo):

```bash
mkdir -p .cursor/rules
curl -o .cursor/rules/model-ids.mdc \
  https://raw.githubusercontent.com/Ahaozandaburada/modelalive/main/.cursor/rules/model-ids.mdc
```

Or symlink from a shared dotfiles repo. The rule activates when editing `.env*`, `modelalive.toml`, and common source/config files.

This repo ships the canonical rule at [`.cursor/rules/model-ids.mdc`](../.cursor/rules/model-ids.mdc).

---

## Agent skill

Project skill (committed with your repo):

```bash
mkdir -p .cursor/skills
cp -R path/to/modelalive/.cursor/skills/model-check .cursor/skills/
```

Personal skill (all your projects):

```bash
mkdir -p ~/.cursor/skills
cp -R path/to/modelalive/.cursor/skills/model-check ~/.cursor/skills/
```

The skill teaches agents to run `check` / `ensure` / `scan` whenever model IDs change. Source: [`.cursor/skills/model-check/SKILL.md`](../.cursor/skills/model-check/SKILL.md).

---

## AGENTS.md for any repo

Drop this block into your project's `AGENTS.md` or `CONTRIBUTING.md`:

```markdown
## LLM model IDs

Before adding or changing model IDs:

1. Run `modelalive check <id>` or `modelalive ensure <id>`
2. Run `modelalive scan .` when unsure where IDs are hardcoded
3. Use `modelalive.ensure()` in application code instead of raw strings

Install: `pip install modelalive` · Docs: https://github.com/Ahaozandaburada/modelalive
```

---

## GitHub Actions (copy-paste)

Pin the action to a release tag in production (`@v1.6.1`), not `@main`.

### 1. Basic gate — fail on retired models

```yaml
name: Model IDs
on: [push, pull_request]

jobs:
  model-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: Ahaozandaburada/modelalive@v1.6.1
        with:
          models: claude-sonnet-4-6 gpt-5.5
          warn-deprecated: "true"
```

### 2. Strict production — fail on unknown IDs too

```yaml
      - uses: Ahaozandaburada/modelalive@v1.6.1
        with:
          models: ${{ vars.LLM_MODEL }}
          strict-unknown: "true"
          warn-deprecated: "true"
```

Set `vars.LLM_MODEL` in repo Settings → Secrets and variables → Actions.

### 3. Config-driven — `modelalive.toml` in repo

`modelalive.toml`:

```toml
models = [
  "claude-sonnet-4-6",
  "gpt-5.5",
]

[ci]
strict_unknown = true
warn_deprecated = true
warn_days = 14
```

Workflow:

```yaml
      - run: pip install "modelalive==1.6.1"

      - run: modelalive check-config
```

Full example: [`examples/github-actions/check-config.yml`](../examples/github-actions/check-config.yml).

### 4. Scan PR for hidden model strings

```yaml
      - run: pip install "modelalive==1.6.1"

      - name: Scan for model IDs
        run: |
          modelalive scan . --json > scan.json
          python - <<'PY'
          import json, sys
          data = json.load(open("scan.json"))
          bad = [h for h in data["findings"] if h.get("status") in ("retired", "deprecated")]
          if bad:
              print("Stale model IDs found:")
              for h in bad:
                  print(f"  {h['path']}:{h['line']} {h['model']} → {h.get('replacement','?')}")
              sys.exit(1)
          print("No retired/deprecated model IDs in scan.")
          PY
```

Full example: [`examples/github-actions/scan-pr.yml`](../examples/github-actions/scan-pr.yml).

### 5. Matrix — multiple providers

```yaml
jobs:
  models:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        model:
          - claude-sonnet-4-6
          - gpt-5.5
          - gemini-3.5-flash
    steps:
      - uses: Ahaozandaburada/modelalive@v1.6.1
        with:
          models: ${{ matrix.model }}
          strict-unknown: "true"
```

Full example: [`examples/github-actions/matrix-providers.yml`](../examples/github-actions/matrix-providers.yml).

### 6. Hosted API (no pip install)

For low-volume checks only (100 requests/month per IP on the public API):

```yaml
      - name: Check model via hosted API
        run: |
          code=$(curl -s -o /dev/null -w "%{http_code}" \
            "https://modelalive.fly.dev/v1/alive?model=claude-sonnet-4-20250514")
          test "$code" != "410" || (echo "Model retired" && exit 1)
```

Prefer the Action or `pip install` for reliability and offline CI.

---

## Pre-commit

Merge [`examples/pre-commit-modelalive.yaml`](../examples/pre-commit-modelalive.yaml) into your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: modelalive-check-config
        name: modelalive check-config
        entry: bash -c 'pip install -q "modelalive==1.6.1" && modelalive check-config'
        language: system
        pass_filenames: false
        files: modelalive.toml
```

Requires `modelalive.toml` at repo root. For `.env.example` checks, see the optional hook in the same example file.

---

## Application integration

### Python (recommended)

```python
import modelalive

MODEL = modelalive.ensure(os.environ.get("LLM_MODEL", "claude-sonnet-4-6"))
```

### TypeScript

```typescript
import { ensure } from "modelalive";

export const MODEL = ensure(process.env.LLM_MODEL ?? "gpt-5.5");
```

### LiteLLM

```python
from modelalive.integrations.litellm import patch_litellm
patch_litellm()  # validates model on each completion call
```

---

## Behavioral stability (ghost drift)

Catch silent backend changes under the same model ID:

```yaml
- uses: Ahaozandaburada/modelalive@v1.6.1
  with:
    models: claude-sonnet-4-6
    stable-baseline: .modelalive/stable.json
    stable-threshold: "0.25"
  env:
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

Record baselines once, commit `.modelalive/*.json`, re-check in CI. Full guide: [STABLE.md](STABLE.md).

---

## Spread the rule

1. Star the repo and link `modelalive check` in your README
2. Add the Cursor rule + skill to your main app repo
3. Pin `Ahaozandaburada/modelalive@v1.6.1` in CI
4. Open a PR on agent templates (LangChain, CrewAI, etc.) pointing here

Questions or missing provider? [Open an issue](https://github.com/Ahaozandaburada/modelalive/issues).
