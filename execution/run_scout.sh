#!/bin/bash
set -e
PRODUCT_ID=${1:-1}
cd "$(dirname "$0")/.."
cd backend
source .venv/bin/activate 2>/dev/null || true
python -c "
import sys
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()
from src.ingestion.scout_runner import ScoutRunner
result = ScoutRunner().run(product_id=int('${PRODUCT_ID}'), triggered_by='manual')
print(f'Scout complete: {result}')
"
