"""
Pydantic schemas for the feedback API endpoints.
"""

from pydantic import BaseModel


class FeedbackItem(BaseModel):
    """Classified feedback item for list views (no raw content)."""

    id: int
    raw_feedback_id: int
    category: str
    sentiment: float
    summary: str
    topics: list[str]
    confidence: float
    llm_provider: str
    classified_at: str
    source: str
    source_ref: str
    external_id: str
    author: str | None
    url: str | None
    score: int | None
    fetched_at: str


class FeedbackDetailItem(FeedbackItem):
    """Classified feedback item for detail views — includes raw content."""

    content: str
    product_id: int


class FeedbackPage(BaseModel):
    """Paginated response wrapper for feedback list endpoint."""

    items: list[FeedbackItem]
    total: int
    page: int
    page_size: int
    pages: int
