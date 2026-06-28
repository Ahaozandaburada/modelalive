# Deploy & publish

## GitHub Actions

CI runs on every push to `main`. Publish and Deploy run on `v*` tags.

If workflows fail with **"account is locked due to a billing issue"**, fix billing at GitHub → Settings → Billing, then re-run the workflow.

Required secrets:

| Secret | Used by |
|--------|---------|
| `FLY_API_TOKEN` | Deploy API → Fly.io |
| `NPM_TOKEN` | npm publish |
| PyPI trusted publisher | `publish.yml` pypi job (OIDC, no token) |

## Publish manually

### PyPI

```bash
python scripts/merge_seeds.py
python scripts/sync_registry.py
pip install build twine
python -m build
twine upload dist/modelalive-*.whl dist/modelalive-*.tar.gz
```

### npm

```bash
python scripts/sync_registry.py
cp modelalive/data/models.json js/registry.json
cd js && npm ci && npm run build && npm publish --access public
```

### Git tag (triggers CI when billing is fixed)

```bash
git tag v1.0.2 && git push origin v1.0.2
```

## Fly.io

```bash
fly auth login
fly launch --copy-config   # first time
fly secrets set MODELALIVE_RATE_LIMIT=120
fly secrets set MODELALIVE_REQUIRE_API_KEY=1
fly secrets set MODELALIVE_API_KEYS="ma_live_your_key"
fly deploy
```

Health check: `https://modelalive-api.fly.dev/v1/health`

## Docker (self-host)

```bash
docker build -t modelalive-api .
docker run -p 8080:8080 \
  -e MODELALIVE_RATE_LIMIT=60 \
  modelalive-api
```

See [HOSTED_API.md](HOSTED_API.md) for all environment variables.
