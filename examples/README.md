# Model Alive — copy-paste examples

Pick a starting point and drop it into your repo.

| Example | What it shows |
|---------|----------------|
| [**quickstart-fastapi/**](quickstart-fastapi/) | `ensure()` before every HTTP chat call (mock or OpenAI) |
| [**quickstart-stable/**](quickstart-stable/) | Stable baseline + GitHub Action drift gate |
| [**github-actions/**](github-actions/) | CI workflows (basic, matrix, scan, stable) |
| [**openai_preflight.py**](openai_preflight.py) | Wrap OpenAI client |
| [**langchain_preflight.py**](langchain_preflight.py) | LangChain integration |
| [**litellm_preflight.py**](litellm_preflight.py) | LiteLLM `patch_litellm()` |
| [**modelalive.toml**](modelalive.toml) | Project config + `check-config` |
| [**baselines/**](baselines/) | Example Stable fingerprint JSON files |
| [**pre-commit-modelalive.yaml**](pre-commit-modelalive.yaml) | Pre-commit hooks |

## 60-second terminal demo

```bash
pip install modelalive
modelalive check claude-sonnet-4-20250514    # exit 1 — retired
modelalive ensure claude-sonnet-4-20250514   # → claude-sonnet-4-6
modelalive check ollama/llama3.2:latest      # universal resolve
```

Record a GIF: [`../scripts/record_demo.sh`](../scripts/record_demo.sh)
