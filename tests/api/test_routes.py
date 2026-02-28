import json
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    insights_dir = tmp_path / "insights"
    insights_dir.mkdir()

    demo = [
        {
            "topic_id": 1, "headline": "TFSA confusion", "category": "friction",
            "confidence": "high", "summary": "Users confused.",
            "evidence": '"quote one" | "quote two"',
            "product_action": "Add calculator", "volume_signal": "47 posts",
            "needs_human_review": True, "review_reason": "CRA risk",
            "canadian_context": None, "n_posts": 47, "top_words": "tfsa", "status": "pending",
        },
        {
            "topic_id": 2, "headline": "Round-ups loved", "category": "win",
            "confidence": "high", "summary": "Users love round-ups.",
            "evidence": '"great feature"',
            "product_action": "Extend to RRSP", "volume_signal": "89 posts",
            "needs_human_review": False, "review_reason": None,
            "canadian_context": None, "n_posts": 89, "top_words": "round", "status": "pending",
        },
    ]
    (insights_dir / "insights.json").write_text(json.dumps(demo))

    import api.data as data_module
    monkeypatch.setattr(data_module, "DEFAULT_DATA_DIR", insights_dir)

    from api.main import app
    return TestClient(app)


def test_get_stats(client):
    r = client.get("/api/stats")
    assert r.status_code == 200
    data = r.json()
    assert data["total_insights"] == 2
    assert data["total_posts"] == 136
    assert data["pending_review"] == 2
    assert data["flagged_for_review"] == 1


def test_get_insights(client):
    r = client.get("/api/insights")
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 2
    assert items[0]["id"] == "1"
    assert items[0]["post_count"] == 47


def test_get_insights_filter_by_category(client):
    r = client.get("/api/insights?category=win")
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 1
    assert items[0]["category"] == "win"


def test_get_insight_by_id(client):
    r = client.get("/api/insights/1")
    assert r.status_code == 200
    assert r.json()["headline"] == "TFSA confusion"


def test_get_insight_not_found(client):
    r = client.get("/api/insights/999")
    assert r.status_code == 404


def test_patch_review(client):
    r = client.patch("/api/reviews/1", json={"status": "known_issue", "note": "JIRA-42"})
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "known_issue"
    assert data["note"] == "JIRA-42"
    assert data["insight_id"] == "1"


def test_get_reviews_after_patch(client):
    client.patch("/api/reviews/1", json={"status": "dismissed", "note": ""})
    r = client.get("/api/reviews")
    assert r.status_code == 200
    reviews = r.json()
    assert any(rv["insight_id"] == "1" for rv in reviews)
