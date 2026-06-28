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
