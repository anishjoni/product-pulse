from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.db import Base
from api.orm_models import InsightORM, RawPost, ReviewORM


def make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_create_insight():
    session = make_session()
    insight = InsightORM(
        id="1",
        headline="TFSA confusion",
        category="friction",
        confidence="high",
        summary="Users confused.",
        evidence='["quote one", "quote two"]',
        product_action="Add calculator",
        volume_signal="47 posts",
        needs_human_review=True,
        post_count=47,
    )
    session.add(insight)
    session.commit()
    result = session.get(InsightORM, "1")
    assert result.headline == "TFSA confusion"
    assert result.post_count == 47


def test_create_review():
    session = make_session()
    insight = InsightORM(
        id="1",
        headline="TFSA confusion",
        category="friction",
        confidence="high",
        summary="Users confused.",
        evidence="[]",
        product_action="Add calculator",
        volume_signal="47 posts",
        needs_human_review=False,
        post_count=47,
    )
    session.add(insight)
    session.commit()
    review = ReviewORM(insight_id="1", status="known_issue", note="JIRA-42")
    session.add(review)
    session.commit()
    assert session.query(ReviewORM).count() == 1
    r = session.query(ReviewORM).first()
    assert r.status == "known_issue"


def test_create_raw_post():
    session = make_session()
    post = RawPost(
        id="post_1",
        text="Love Wealthsimple!",
        timestamp=datetime(2024, 1, 1),
        source="reddit",
    )
    session.add(post)
    session.commit()
    result = session.get(RawPost, "post_1")
    assert result.source == "reddit"
