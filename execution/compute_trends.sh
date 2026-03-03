#!/bin/bash
# compute_trends.sh — Run the TrendAnalyser for a product and print results.
#
# Usage:
#   ./execution/compute_trends.sh [PRODUCT_ID]
#
# PRODUCT_ID defaults to 1 if not provided.
#
# Examples:
#   ./execution/compute_trends.sh        # product 1
#   ./execution/compute_trends.sh 2      # product 2
set -e

PRODUCT_ID=${1:-1}

# Navigate to project root (one level up from the execution/ directory),
# then into the backend package.
cd "$(dirname "$0")/.."
cd backend

source .venv/bin/activate 2>/dev/null || true

python -c "
import sys
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()
from src.analysis.trend_analyser import TrendAnalyser
trends = TrendAnalyser().compute_trends(product_id=int('${PRODUCT_ID}'))
print(f'Found {len(trends)} trends:')
for t in trends[:10]:
    print(f'  {t[\"topic\"]}: {t[\"current_count\"]} mentions, +{t[\"pct_change\"]:.0f}%')
"
