# modelalive (JavaScript)

Universal LLM pre-flight gate — **Alive** (lifecycle) + **Stable** (behavioral drift) for 765+ models.

TypeScript/JavaScript SDK for [Model Alive](https://github.com/Ahaozandaburada/modelalive).

## Install

```bash
npm install modelalive
```

## Usage

```typescript
import { alive, ensure, resolve } from "modelalive";
import { compareFingerprints, assertStable } from "modelalive";

// Lifecycle gate
ensure("openrouter/anthropic/claude-sonnet-4-6"); // → "claude-sonnet-4-6"

// Behavioral drift (Stable)
const report = compareFingerprints(baseline, current, 0.25);
assertStable(baseline, current);
```

See [docs/STABLE.md](https://github.com/Ahaozandaburada/modelalive/blob/main/docs/STABLE.md) and [docs/UNIVERSAL.md](https://github.com/Ahaozandaburada/modelalive/blob/main/docs/UNIVERSAL.md).

Registry + stable prompts bundled at build time.
