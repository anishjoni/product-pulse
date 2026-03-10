#!/usr/bin/env bash
# Discover and optionally add feedback sources for a product.
#
# Usage (from project root):
#   bash execution/discover_sources.sh "Mintlify"
#   bash execution/discover_sources.sh "Mintlify" --add --product-id 3
#   bash execution/discover_sources.sh "Wealthsimple" --country ca --add
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT/backend"

exec uv run python "$REPO_ROOT/execution/discover_sources.py" "$@"
