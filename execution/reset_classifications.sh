#!/usr/bin/env bash
# Reset all classified_feedback and trends rows so classify_backfill.sh
# will re-classify everything from scratch with the current OLLAMA_MODEL.
#
# Usage: bash execution/reset_classifications.sh [product_id]
#   product_id defaults to 1
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$REPO_ROOT/backend"
cd "$BACKEND"
export DATABASE_URL="${DATABASE_URL:-sqlite:///./data/pulse.db}"
PRODUCT_ID="${1:-1}"

uv run python - "$PRODUCT_ID" <<'PYEOF'
import sys, sqlite3
sys.path.insert(0, ".")

product_id = int(sys.argv[1])

conn = sqlite3.connect("data/pulse.db")
conn.row_factory = sqlite3.Row

# Count before
cf_before = conn.execute(
    "SELECT COUNT(*) FROM classified_feedback cf "
    "JOIN raw_feedback rf ON rf.id = cf.raw_feedback_id "
    "WHERE rf.product_id = ?", (product_id,)
).fetchone()[0]
tr_before = conn.execute(
    "SELECT COUNT(*) FROM trends WHERE product_id = ?", (product_id,)
).fetchone()[0]

# Delete trends first (no FK dependency on classified_feedback, but stale after reset)
conn.execute("DELETE FROM trends WHERE product_id = ?", (product_id,))

# Delete classified_feedback for this product's raw_feedback
conn.execute(
    "DELETE FROM classified_feedback WHERE raw_feedback_id IN ("
    "  SELECT id FROM raw_feedback WHERE product_id = ?"
    ")", (product_id,)
)
conn.commit()

print(f"Reset complete for product_id={product_id}.")
print(f"  Deleted {cf_before} classified_feedback rows.")
print(f"  Deleted {tr_before} trends rows.")
print(f"  raw_feedback rows untouched — ready for backfill.")
PYEOF
