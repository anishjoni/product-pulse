from typing import Literal

from pydantic import BaseModel

CategoryType = Literal["roadmap", "friction", "win", "other"]
ConfidenceType = Literal["high", "medium", "low"]
StatusType = Literal[
    "pending",
    "escalate_to_product",
    "under_investigation",
    "known_issue",
    "out_of_scope",
    "dismissed",
]


class Insight(BaseModel):
    id: str
    headline: str
    category: CategoryType
    confidence: ConfidenceType
    summary: str
    evidence: list[str]
    product_action: str
    volume_signal: str
    needs_human_review: bool
    review_reason: str | None
    canadian_context: str | None
    post_count: int


class Review(BaseModel):
    insight_id: str
    status: StatusType
    note: str
    updated_at: str


class ReviewUpdate(BaseModel):
    status: StatusType
    note: str = ""


class Stats(BaseModel):
    total_posts: int
    total_insights: int
    pending_review: int
    flagged_for_review: int
