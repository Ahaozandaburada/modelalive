# modelalive (JavaScript)

TypeScript/JavaScript SDK for [Model Alive](https://github.com/Ahaozandaburada/modelalive).

## Install

```bash
npm install modelalive
```

*(npm publish pending — build from source:)*

```bash
npm install
npm run build
```

## Usage

```typescript
import { alive, check, ensure, resolve } from "modelalive";

// Non-throwing check
const result = alive("claude-sonnet-4-20250514");
console.log(result.status);       // "retired"
console.log(result.replacement); // "claude-sonnet-4-6"

// Pre-flight before API call
const safe = ensure("claude-sonnet-4-20250514"); // "claude-sonnet-4-6"

// Full replacement chain
resolve("gemini-2.0-flash"); // "gemini-3.5-flash"

// Strict mode (throws on unknown)
check("unknown-model", { strictUnknown: true });
```

Registry is bundled at build time from `registry/models.json`.
