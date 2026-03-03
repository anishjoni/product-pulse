"""
Pydantic schemas for the products API endpoints.
"""

from pydantic import BaseModel


class ProductSourceIn(BaseModel):
    source_type: str  # "reddit" | "youtube" | "twitter"
    source_ref: str


class ProductCreateRequest(BaseModel):
    name: str
    slug: str
    description: str | None = None
    keywords: list[str]
    sources: list[ProductSourceIn]


class ProductUpdateRequest(BaseModel):
    keywords: list[str]
    sources: list[ProductSourceIn]


class ProductResponse(BaseModel):
    id: int
    name: str
    slug: str
    description: str | None
    is_active: bool
    created_at: str
    keywords: list[str]
    sources: list[dict]


class ProductSummaryResponse(BaseModel):
    product_id: int
    product_name: str
    period: str
    total_items: int
    category_counts: dict[str, int]
    avg_sentiment: float
    sentiment_trend: str  # "improving" | "declining" | "stable"
    top_trend: str | None
    last_scout_at: str | None
    last_scout_status: str | None
