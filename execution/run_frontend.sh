#!/usr/bin/env bash
# Run the Product Pulse Next.js dev server.
# Usage: bash execution/run_frontend.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FRONTEND="$REPO_ROOT/frontend"

export NVM_DIR="$HOME/.nvm"
# shellcheck source=/dev/null
[ -s "$NVM_DIR/nvm.sh" ] && source "$NVM_DIR/nvm.sh"

if ! command -v node &>/dev/null; then
  echo "ERROR: Node.js not found. Run: nvm install 20"
  exit 1
fi

cd "$FRONTEND"
exec npm run dev
