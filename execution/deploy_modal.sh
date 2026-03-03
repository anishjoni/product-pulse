#!/usr/bin/env bash
# Deploy the Product Pulse backend to Modal.
#
# Prerequisites:
#   pip install modal
#   modal setup              # authenticate once
#   modal secret create product-pulse-secrets KEY=value ...
#
# Usage:
#   bash execution/deploy_modal.sh [--dry-run]
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$REPO_ROOT/backend"

# Activate backend venv so modal CLI is available (if installed there)
VENV="$BACKEND/.venv"
if [[ -d "$VENV" ]]; then
  # shellcheck source=/dev/null
  source "$VENV/bin/activate" 2>/dev/null || true
fi

if ! command -v modal &>/dev/null; then
  echo "ERROR: modal not found. Install with: pip install modal"
  exit 1
fi

cd "$BACKEND"

if [[ "${1:-}" == "--dry-run" ]]; then
  echo "Dry run — skipping actual deploy."
  modal app list
else
  echo "Deploying product-pulse-backend to Modal..."
  modal deploy modal_app.py
  echo ""
  echo "Done. Copy the printed URL and set it as NEXT_PUBLIC_API_BASE in:"
  echo "  - frontend/.env.local (local dev)"
  echo "  - Vercel dashboard environment variables (production)"
fi
