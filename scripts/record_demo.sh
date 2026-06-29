#!/usr/bin/env bash
# Terminal demo for README / asciinema. Run from repo root.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if ! command -v modelalive >/dev/null 2>&1; then
  pip install -q -e . 2>/dev/null || pip install -q modelalive
fi

run_demo() {
  clear
  echo "=== Model Alive — 60 second demo ==="
  echo
  sleep 0.5

  echo '$ pip install modelalive'
  echo '(already installed)'
  echo
  sleep 0.8

  echo '$ modelalive check claude-sonnet-4-20250514'
  modelalive check claude-sonnet-4-20250514 || true
  echo
  sleep 1.2

  echo '$ modelalive ensure claude-sonnet-4-20250514'
  modelalive ensure claude-sonnet-4-20250514
  echo
  sleep 1.2

  echo '$ modelalive check ollama/llama3.2:latest'
  modelalive check ollama/llama3.2:latest
  echo
  sleep 1.2

  echo '$ modelalive stable prompts | head -3'
  modelalive stable prompts 2>/dev/null | head -3
  echo
  sleep 0.8

  echo "=== Done. Docs: https://github.com/Ahaozandaburada/modelalive ==="
}

if [[ "${1:-}" == "--cast" ]]; then
  if ! command -v asciinema >/dev/null 2>&1; then
    echo "Install asciinema: brew install asciinema" >&2
    exit 1
  fi
  OUT="${ROOT}/docs/marketing/modelalive-demo.cast"
  asciinema rec "$OUT" -c "bash '$0'"
  echo "Saved: $OUT"
  echo "Upload: asciinema upload $OUT"
else
  run_demo
fi
