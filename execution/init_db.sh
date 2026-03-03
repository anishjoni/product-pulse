#!/bin/bash
set -e
cd "$(dirname "$0")/.."
cd backend
source .venv/bin/activate 2>/dev/null || true
python -m src.db.init_db
python -m src.db.seed
echo "Database initialised and seeded."
