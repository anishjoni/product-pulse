"""Load/save insight data from the JSON files written by the pipeline."""

import json
from datetime import datetime
from pathlib import Path

from api.models import Insight, Review, ReviewUpdate

_STATUS_TO_FILE = {
    "escalate_to_product": "escalate to product",
    "under_investigation": "under investigation",
    "known_issue": "known issue",
    "out_of_scope": "out of scope",
}
_STATUS_FROM_FILE = {v: k for k, v in _STATUS_TO_FILE.items()}

DEFAULT_DATA_DIR = Path("data/insights")


def _parse_evidence(raw: str | list) -> list[str]:
    if isinstance(raw, list):
        return raw
    return [s.strip() for s in str(raw).split("|") if s.strip()]


def _normalize_status(action: str) -> str:
    return _STATUS_FROM_FILE.get(action, action)


def _denormalize_status(status: str) -> str:
    return _STATUS_TO_FILE.get(status, status)


def load_insights(data_dir: Path = DEFAULT_DATA_DIR) -> list[Insight]:
    path = data_dir / "insights.json"
    if not path.exists():
        return _demo_insights()
    raw = json.loads(path.read_text())
    if not raw:
        return _demo_insights()
    return [
        Insight(
            id=str(item["topic_id"]),
            headline=item["headline"],
            category=item["category"],
            confidence=item["confidence"],
            summary=item["summary"],
            evidence=_parse_evidence(item.get("evidence", "")),
            product_action=item["product_action"],
            volume_signal=item["volume_signal"],
            needs_human_review=item.get("needs_human_review", False),
            review_reason=item.get("review_reason"),
            canadian_context=item.get("canadian_context"),
            post_count=item.get("n_posts", 0),
        )
        for item in raw
    ]


def load_review_log(data_dir: Path = DEFAULT_DATA_DIR) -> list[Review]:
    path = data_dir / "review_log.json"
    if not path.exists():
        return []
    raw: dict = json.loads(path.read_text())
    return [
        Review(
            insight_id=insight_id,
            status=_normalize_status(entry.get("action", "pending")),
            note=entry.get("note", ""),
            updated_at=entry.get("reviewed_at", ""),
        )
        for insight_id, entry in raw.items()
    ]


def save_review(insight_id: str, update: ReviewUpdate, data_dir: Path = DEFAULT_DATA_DIR) -> Review:
    path = data_dir / "review_log.json"
    log: dict = json.loads(path.read_text()) if path.exists() else {}
    now = datetime.now().isoformat()
    log[insight_id] = {
        "action": _denormalize_status(update.status),
        "note": update.note,
        "reviewed_at": now,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(log, indent=2))
    return Review(insight_id=insight_id, status=update.status, note=update.note, updated_at=now)


def _demo_insights() -> list[Insight]:
    return [
        Insight(
            id="1",
            headline="TFSA over-contribution limits confusing users",
            category="friction",
            confidence="high",
            summary="Users are confused about annual TFSA contribution limits, leading to over-contributions and CRA penalties.",
            evidence=[
                '"I got a penalty letter from CRA — had no idea I over-contributed."',
                '"WS should warn me when I\'m close to my TFSA limit."',
            ],
            product_action="Add real-time TFSA contribution tracker with CRA limit warnings.",
            volume_signal="47 posts over 6 months",
            needs_human_review=True,
            review_reason="CRA penalty implications — validate with compliance before acting",
            canadian_context="2024 TFSA limit is $7,000; lifetime room varies by year of eligibility",
            post_count=47,
        ),
        Insight(
            id="2",
            headline="Instant deposit limits too low for active traders",
            category="friction",
            confidence="high",
            summary="Users want higher instant deposit limits. Current $1,500 limit frustrates active traders missing same-day opportunities.",
            evidence=[
                '"$1,500 instant limit is a joke when you\'re trying to catch a dip."',
                '"Questrade gives me $3,000 instant — why is WS so low?"',
            ],
            product_action="Review instant deposit risk model. Consider tiered limits based on account history.",
            volume_signal="62 posts, consistent complaints",
            needs_human_review=False,
            review_reason=None,
            canadian_context="Instant deposit is a key differentiator vs Questrade for active traders",
            post_count=62,
        ),
    ]
