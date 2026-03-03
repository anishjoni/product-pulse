#!/usr/bin/env bash
# Classify all raw_feedback rows that have no classified_feedback entry yet.
# Useful after Ollama/Gemini quota failures that left items unclassified.
#
# Usage: bash execution/classify_backfill.sh [product_id]
#   product_id defaults to 1
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$REPO_ROOT/backend"
PY="$BACKEND/.venv/bin/python3"

cd "$BACKEND"
export DATABASE_URL="${DATABASE_URL:-sqlite:///./data/pulse.db}"
# Force Ollama-only during backfill — avoids burning Gemini free-tier quota.
# Unset to re-enable Gemini fallback.
export OLLAMA_ONLY="${OLLAMA_ONLY:-1}"
PRODUCT_ID="${1:-1}"

"$PY" - "$PRODUCT_ID" <<'PYEOF'
import sys, logging
sys.path.insert(0, ".")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("backfill")

product_id = int(sys.argv[1])

from src.db.database import get_db
from src.db.repositories.product_repository import ProductRepository
from src.db.repositories.classified_feedback_repository import ClassifiedFeedbackRepository
from src.llm.classifier import LLMClassifier
from src.analysis.trend_analyser import TrendAnalyser

product = ProductRepository().get_by_id(product_id)
if not product:
    logger.error("Product %d not found.", product_id)
    sys.exit(1)

# Find all raw_feedback rows for this product with no classified_feedback entry
with get_db() as conn:
    rows = conn.execute(
        """
        SELECT rf.*
        FROM raw_feedback rf
        LEFT JOIN classified_feedback cf ON cf.raw_feedback_id = rf.id
        WHERE rf.product_id = ?
          AND (cf.id IS NULL OR cf.classification_status = 'failed')
        ORDER BY rf.id
        """,
        (product_id,),
    ).fetchall()

items = [dict(r) for r in rows]
logger.info("Found %d unclassified items for product '%s'.", len(items), product["name"])

if not items:
    logger.info("Nothing to backfill. All done.")
    sys.exit(0)

classifier = LLMClassifier()
cf_repo = ClassifiedFeedbackRepository()

ok = fail = 0
for i, raw_item in enumerate(items, 1):
    result = classifier.classify(raw_item, product)
    if result["classification_status"] == "success":
        cf_repo.insert(
            raw_feedback_id=raw_item["id"],
            category=result["category"],
            sentiment=result["sentiment"],
            summary=result["summary"],
            topics=result["topics"],
            confidence=result["confidence"],
            llm_provider=result["llm_provider"],
        )
        ok += 1
    else:
        cf_repo.insert_failed(raw_item["id"], result["llm_provider"])
        fail += 1

    if i % 10 == 0 or i == len(items):
        logger.info("Progress: %d/%d  (ok=%d  fail=%d)", i, len(items), ok, fail)

logger.info("Backfill complete. Classified=%d, Failed=%d", ok, fail)

# Recompute trends with fresh data
try:
    trends = TrendAnalyser().compute_trends(product_id=product_id)
    logger.info("Trends recomputed: %d topics.", len(trends))
except Exception as e:
    logger.warning("Trend computation failed (non-fatal): %s", e)
PYEOF
