#!/usr/bin/env bash
# Run the Product Pulse FastAPI dev server.
# Usage: bash execution/run_api.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$REPO_ROOT/backend"

cd "$BACKEND"

# Load .env if present
if [[ -f "$REPO_ROOT/.env" ]]; then
  set -a; source "$REPO_ROOT/.env"; set +a
fi

PORT="${PORT:-8000}"

exec uv run uvicorn src.api.main:app \
  --host 0.0.0.0 \
  --port "$PORT" \
  --reload
