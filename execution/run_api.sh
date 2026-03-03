#!/usr/bin/env bash
# Run the Product Pulse FastAPI dev server.
# Usage: bash execution/run_api.sh [--port 8000] [--reload]
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$REPO_ROOT/backend"
VENV="$BACKEND/.venv"

if [[ ! -d "$VENV" ]]; then
  echo "ERROR: venv not found at $VENV"
  echo "Run: python3 -m virtualenv $VENV && $VENV/bin/pip install -r $BACKEND/requirements.txt"
  exit 1
fi

cd "$BACKEND"

# Load .env if present
if [[ -f "$REPO_ROOT/.env" ]]; then
  set -a; source "$REPO_ROOT/.env"; set +a
fi

PORT="${PORT:-8000}"
RELOAD_FLAG="--reload"

exec "$VENV/bin/uvicorn" src.api.main:app \
  --host 0.0.0.0 \
  --port "$PORT" \
  $RELOAD_FLAG
