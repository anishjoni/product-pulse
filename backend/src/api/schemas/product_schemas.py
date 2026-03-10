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


class DiscoveredSourceOut(BaseModel):
    source_type: str
    source_ref: str
    display: str
    confidence: str  # "confirmed" | "suggested"


class DiscoverSourcesResponse(BaseModel):
    sources: list[DiscoveredSourceOut]
    keywords: list[str]


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
    source_counts: dict[str, int] = {}


class ProductStatsResponse(BaseModel):
    product_id: int
    period_days: int
    data: list[dict]  # wide format, one row per date


class TopicSentimentResponse(BaseModel):
    topic: str
    total_count: int
    avg_sentiment: float
    categories: dict[str, dict]  # {category: {count, avg_sentiment}}


class TopicCompareItem(BaseModel):
    product_id: int
    product_name: str
    total_count: int
    avg_sentiment: float
    top_category: str | None
    category_breakdown: dict[str, int]


class TopicCompareResponse(BaseModel):
    topic: str
    results: list[TopicCompareItem]
