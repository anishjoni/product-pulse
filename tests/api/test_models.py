from api.models import Insight, Review, ReviewUpdate, Stats


def test_insight_model():
    data = {
        "id": "1",
        "headline": "TFSA over-contribution",
        "category": "friction",
        "confidence": "high",
        "summary": "Users are confused about TFSA limits.",
        "evidence": ["quote one", "quote two"],
        "product_action": "Add in-app limit calculator",
        "volume_signal": "47 posts over 6 months",
        "needs_human_review": True,
        "review_reason": "CRA penalty risk",
        "canadian_context": "TFSA limit is $7000 in 2024",
        "post_count": 47,
    }
    insight = Insight(**data)
    assert insight.id == "1"
    assert insight.category == "friction"
    assert len(insight.evidence) == 2


def test_review_model():
    review = Review(
        insight_id="1",
        status="pending",
        note="",
        updated_at="2024-01-01T00:00:00",
    )
    assert review.status == "pending"


def test_review_update_defaults():
    update = ReviewUpdate(status="known_issue")
    assert update.note == ""


def test_stats_model():
    stats = Stats(total_posts=1000, total_insights=48, pending_review=36, flagged_for_review=4)
    assert stats.pending_review == 36
