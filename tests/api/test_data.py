import json

import pytest

from api.data import load_insights, load_review_log, save_review
from api.models import ReviewUpdate

SAMPLE_INSIGHTS = [
    {
        "topic_id": 1,
        "headline": "TFSA over-contribution",
        "category": "friction",
        "confidence": "high",
        "summary": "Users confused about TFSA limits.",
        "evidence": '"quote one" | "quote two"',
        "product_action": "Add calculator",
        "volume_signal": "47 posts",
        "needs_human_review": True,
        "review_reason": "CRA risk",
        "canadian_context": "TFSA 2024 = $7000",
        "n_posts": 47,
        "top_words": "tfsa, limit, over",
        "status": "pending",
    }
]

SAMPLE_REVIEW_LOG = {
    "1": {"action": "known issue", "note": "JIRA-42", "reviewed_at": "2024-01-01T00:00:00"}
}


@pytest.fixture
def tmp_data_dir(tmp_path):
    insights_dir = tmp_path / "insights"
    insights_dir.mkdir()
    (insights_dir / "insights.json").write_text(json.dumps(SAMPLE_INSIGHTS))
    (insights_dir / "review_log.json").write_text(json.dumps(SAMPLE_REVIEW_LOG))
    return insights_dir


def test_load_insights_maps_fields(tmp_data_dir):
    insights = load_insights(tmp_data_dir)
    assert len(insights) == 1
    i = insights[0]
    assert i.id == "1"
    assert i.post_count == 47
    assert i.evidence == ['"quote one"', '"quote two"']


def test_load_review_log_maps_fields(tmp_data_dir):
    reviews = load_review_log(tmp_data_dir)
    assert len(reviews) == 1
    r = reviews[0]
    assert r.insight_id == "1"
    assert r.status == "known_issue"
    assert r.note == "JIRA-42"
    assert r.updated_at == "2024-01-01T00:00:00"


def test_save_review(tmp_data_dir):
    returned = save_review("1", ReviewUpdate(status="dismissed", note="out of scope"), tmp_data_dir)
    assert returned.insight_id == "1"
    assert returned.status == "dismissed"
    assert returned.note == "out of scope"
    # Also verify it was persisted
    reviews = load_review_log(tmp_data_dir)
    r = next(r for r in reviews if r.insight_id == "1")
    assert r.status == "dismissed"
    assert r.note == "out of scope"


def test_load_insights_falls_back_to_demo_when_missing(tmp_path):
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    insights = load_insights(empty_dir)
    assert len(insights) >= 1
