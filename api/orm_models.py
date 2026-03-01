from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.db import Base


class RawPost(Base):
    __tablename__ = "raw_posts"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    sentiment_score: Mapped[float | None] = mapped_column()
    language: Mapped[str | None] = mapped_column(Text)
    topic_id: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[str | None] = mapped_column(Text)


class InsightORM(Base):
    __tablename__ = "insights"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    headline: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[str] = mapped_column(Text, nullable=False)
    product_action: Mapped[str] = mapped_column(Text, nullable=False)
    volume_signal: Mapped[str] = mapped_column(Text, nullable=False)
    needs_human_review: Mapped[bool] = mapped_column(Boolean, default=False)
    review_reason: Mapped[str | None] = mapped_column(Text)
    canadian_context: Mapped[str | None] = mapped_column(Text)
    post_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    review: Mapped["ReviewORM | None"] = relationship(
        "ReviewORM", back_populates="insight", uselist=False
    )


class ReviewORM(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    insight_id: Mapped[str] = mapped_column(
        Text, ForeignKey("insights.id"), nullable=False, unique=True
    )
    status: Mapped[str] = mapped_column(Text, nullable=False, default="pending")
    note: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    insight: Mapped["InsightORM"] = relationship("InsightORM", back_populates="review")
