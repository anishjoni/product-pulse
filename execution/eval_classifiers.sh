#!/usr/bin/env bash
# Usage: bash execution/eval_classifiers.sh [product_id] [n_samples]
# product_id defaults to 1, n_samples defaults to 100
#
# First run downloads ~700 MB of model weights to ~/.cache/huggingface.
# Subsequent runs use the cache and start immediately.
set -euo pipefail

PRODUCT_ID=${1:-1}
N=${2:-100}

cd "$(dirname "$0")/../backend"

echo "Installing experiment dependencies (torch CPU, transformers, scipy) …"
uv sync --extra experiments

echo "Starting evaluation: product_id=${PRODUCT_ID}, n_samples=${N}"
uv run python -m src.experiments.eval_classifiers "$PRODUCT_ID" "$N"
