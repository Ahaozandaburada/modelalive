# Quickstart — Stable (behavioral drift) in CI

Record a baseline once, then fail CI if the endpoint drifts under the same model ID.

## 1. Record baseline (needs provider API key)

```bash
pip install "modelalive[stable]"

export OPENAI_API_KEY=sk-...
modelalive stable baseline gpt-4o -o .modelalive/stable.json
git add .modelalive/stable.json
```

## 2. GitHub Action (copy to your repo)

See [`../github-actions/stable-check.yml`](../github-actions/stable-check.yml):

```yaml
- uses: Ahaozandaburada/modelalive@v1.6.0
  with:
    models: gpt-4o
    stable-baseline: .modelalive/stable.json
    stable-threshold: "0.25"
  env:
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

## 3. Offline validate (no API key)

```bash
modelalive stable validate .modelalive/stable.json
modelalive stable validate examples/baselines/gpt-4o.json
```

## 4. Weekly cron

```yaml
on:
  schedule:
    - cron: "0 9 * * 1"  # Mondays 09:00 UTC
```

Ghost drift docs: [docs/STABLE.md](../../docs/STABLE.md)
