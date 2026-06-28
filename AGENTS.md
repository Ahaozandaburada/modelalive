# Agent instructions

When this repository or a consumer app touches **LLM model IDs**, use [Model Alive](https://github.com/Ahaozandaburada/modelalive).

## Required workflow

1. `modelalive check <id>` before hardcoding a model string
2. `modelalive ensure <id>` when wiring API clients (auto-replaces retired IDs)
3. `modelalive scan .` when hunting stale IDs across a codebase
4. `modelalive check-config` when `modelalive.toml` exists

## Skill & rule (Cursor)

- **Skill:** `.cursor/skills/model-check/SKILL.md` — load for any model-ID task
- **Rule:** `.cursor/rules/model-ids.mdc` — applies to env/config/source files

Copy both into consumer repos; see [docs/ADOPTION.md](docs/ADOPTION.md).

## Strict mode

Set `MODELALIVE_STRICT=1` in CI so unknown model IDs fail the build.

## Do not guess replacements

Use `modelalive resolve <id>` or the API `replacement` field — provider deprecations change frequently.
