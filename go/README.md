# Model Alive — Go SDK

Pre-flight check: is this LLM model ID still alive?

```go
import (
    "time"

    "github.com/Ahaozandaburada/modelalive/go/modelalive"
)

func main() {
    today := time.Now().UTC()
    res, _ := modelalive.Alive("claude-sonnet-4-20250514", today)
    // res.Status == "retired"

    safe, _ := modelalive.Ensure("claude-sonnet-4-20250514", today)
    // safe == "claude-sonnet-4-6"
}
```

## Install

```bash
go get github.com/Ahaozandaburada/modelalive/go/modelalive@latest
```

Registry is embedded in the module — no network required at runtime.

## Stable (behavioral drift)

```go
prompts, _ := modelalive.ListStablePrompts()
responses := map[string][]string{}
for _, p := range prompts {
    responses[p.ID] = []string{"fixture-response"}
}
base, _ := modelalive.FingerprintFromResponses("gpt-4o", responses, nil, 1)
cur, _ := modelalive.FingerprintFromResponses("gpt-4o", responses, nil, 1)
report := modelalive.CompareFingerprints(base, cur, 0.25)
// report.Stable == true
```
