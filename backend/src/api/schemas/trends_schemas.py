"""
Pydantic schemas for the trends API endpoints.
"""

from typing import Optional

from pydantic import BaseModel


class TrendItem(BaseModel):
    """A single trending topic with its counts and breakdown."""

    topic: str
    current_count: int
    previous_count: int
    pct_change: float
    category_breakdown: dict[str, int]


class TrendsResponse(BaseModel):
    """Response schema for GET /products/{product_id}/trends."""

    product_id: int
    trends: list[TrendItem]
    computed_at: Optional[str]
    period_days: int
