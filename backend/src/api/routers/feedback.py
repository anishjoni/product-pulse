"""
Feedback router — endpoints for browsing classified feedback items.

Routes:
    GET /products/{product_id}/feedback   — paginated, filtered feedback list
    GET /feedback/{feedback_id}           — single item with full raw content
"""

import math

from fastapi import APIRouter, HTTPException, Query

from src.api.schemas.feedback_schemas import FeedbackDetailItem, FeedbackItem, FeedbackPage
from src.db.repositories.classified_feedback_repository import ClassifiedFeedbackRepository
from src.db.repositories.product_repository import ProductRepository

router = APIRouter()

_product_repo = ProductRepository()
_feedback_repo = ClassifiedFeedbackRepository()


@router.get(
    "/products/{product_id}/feedback",
    response_model=FeedbackPage,
    summary="List classified feedback for a product",
)
def list_feedback(
    product_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    category: str | None = Query(
        default=None,
        description="feature_request | bug_report | complaint | praise | general_discussion",
    ),
    source: str | None = Query(default=None, description="reddit | youtube"),
    sentiment: str | None = Query(
        default=None, description="positive | negative | neutral"
    ),
    search: str | None = Query(default=None, description="Substring search on content/summary"),
    date_from: str | None = Query(default=None, description="YYYY-MM-DD lower bound"),
    date_to: str | None = Query(default=None, description="YYYY-MM-DD upper bound"),
):
    """
    Return a paginated, filterable list of classified feedback for a product.
    Items are sorted newest first.
    """
    product = _product_repo.get_by_id(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    items, total = _feedback_repo.get_paginated(
        product_id=product_id,
        page=page,
        page_size=page_size,
        category=category,
        source=source,
        sentiment=sentiment,
        search=search,
        date_from=date_from,
        date_to=date_to,
    )

    return FeedbackPage(
        items=[FeedbackItem(**item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, math.ceil(total / page_size)),
    )


@router.get(
    "/feedback/{feedback_id}",
    response_model=FeedbackDetailItem,
    summary="Get full detail for one feedback item",
)
def get_feedback(feedback_id: int):
    """Return a single classified feedback item including its raw content."""
    item = _feedback_repo.get_by_id(feedback_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Feedback item not found")
    return FeedbackDetailItem(**item)
