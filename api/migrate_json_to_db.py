"""One-time migration: load data/insights/insights.json + review_log.json into DB."""

import json
from pathlib import Path

from api.data import _normalize_status, _parse_evidence
from api.db import Base, SessionLocal, engine
from api.orm_models import InsightORM, ReviewORM

INSIGHTS_PATH = Path("data/insights/insights.json")
REVIEW_LOG_PATH = Path("data/insights/review_log.json")


def migrate():
    Base.metadata.create_all(engine)
    db = SessionLocal()

    if INSIGHTS_PATH.exists():
        raw = json.loads(INSIGHTS_PATH.read_text())
        for item in raw:
            iid = str(item["topic_id"])
            if db.get(InsightORM, iid):
                continue
            evidence = _parse_evidence(item.get("evidence", ""))
            db.add(
                InsightORM(
                    id=iid,
                    headline=item["headline"],
                    category=item["category"],
                    confidence=item["confidence"],
                    summary=item["summary"],
                    evidence=json.dumps(evidence),
                    product_action=item["product_action"],
                    volume_signal=item["volume_signal"],
                    needs_human_review=item.get("needs_human_review", False),
                    review_reason=item.get("review_reason"),
                    canadian_context=item.get("canadian_context"),
                    post_count=item.get("n_posts", 0),
                )
            )

    if REVIEW_LOG_PATH.exists():
        log = json.loads(REVIEW_LOG_PATH.read_text())
        for iid, entry in log.items():
            if db.query(ReviewORM).filter_by(insight_id=iid).first():
                continue
            db.add(
                ReviewORM(
                    insight_id=iid,
                    status=_normalize_status(entry.get("action", "pending")),
                    note=entry.get("note", ""),
                )
            )

    db.commit()
    db.close()
    print("Migration complete.")


if __name__ == "__main__":
    migrate()
