# Contributing

## Registry changes

1. Edit provider seed in `registry/seeds/{provider}.json` (preferred) or `registry/models.json`
2. Run `python scripts/merge_seeds.py && python scripts/sync_registry.py`
3. Run `modelalive validate --strict && pytest -q`
4. Open a PR — CI must pass

Every model entry needs:

- `status`, `provider`, `source`, `migrate_url`
- For retired/deprecated: `replacement`, `retired_at`

## Tests

```bash
pip install -e ".[dev]"
pytest -q
```

Target: no false positives on tier-1 providers. See [ACCURACY.md](docs/ACCURACY.md).

## TypeScript SDK

```bash
cd js && npm ci && npm run build && node dist/smoke.test.js
```

## Release

1. Bump `pyproject.toml` + `modelalive/__init__.py`
2. Update `CHANGELOG.md`
3. `python scripts/merge_seeds.py && python scripts/sync_registry.py`
4. `pytest -q && python -m build`
5. `twine upload dist/*`
6. `gh release create vX.Y.Z`
