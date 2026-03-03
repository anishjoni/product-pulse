"""
Products router — CRUD endpoints for product configuration.
"""

from fastapi import APIRouter, HTTPException, Query

from src.api.schemas.product_schemas import (
    ProductCreateRequest,
    ProductResponse,
    ProductSummaryResponse,
    ProductUpdateRequest,
)
from src.db.repositories.classified_feedback_repository import ClassifiedFeedbackRepository
from src.db.repositories.product_repository import ProductRepository
from src.db.repositories.scout_run_repository import ScoutRunRepository
from src.db.repositories.trends_repository import TrendsRepository

router = APIRouter()
repo = ProductRepository()
_feedback_repo = ClassifiedFeedbackRepository()
_run_repo = ScoutRunRepository()
_trends_repo = TrendsRepository()


@router.get("/products", response_model=list[ProductResponse])
def list_products():
    """Return all active products with their keywords and sources."""
    return repo.get_all_active()


@router.post("/products", response_model=ProductResponse, status_code=201)
def create_product(payload: ProductCreateRequest):
    """Create a new product with keywords and sources."""
    sources = [s.model_dump() for s in payload.sources]
    product = repo.create(
        name=payload.name,
        slug=payload.slug,
        description=payload.description,
        keywords=payload.keywords,
        sources=sources,
    )
    return product


@router.get("/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: int):
    """Return a single product by ID, or 404 if not found."""
    product = repo.get_by_id(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.put("/products/{product_id}", response_model=ProductResponse)
def update_product(product_id: int, payload: ProductUpdateRequest):
    """Replace keywords and sources for an existing product."""
    product = repo.get_by_id(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    sources = [s.model_dump() for s in payload.sources]
    repo.update_keywords(product_id, payload.keywords)
    repo.update_sources(product_id, sources)

    updated = repo.get_by_id(product_id)
    return updated


@router.delete("/products/{product_id}", status_code=204)
def delete_product(product_id: int):
    """Soft-delete a product (sets is_active=0)."""
    product = repo.get_by_id(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    repo.soft_delete(product_id)


@router.get("/products/{product_id}/summary", response_model=ProductSummaryResponse)
def get_product_summary(
    product_id: int,
    period_days: int = Query(default=7, ge=1, le=30),
):
    """Return a pulse overview for the dashboard header."""
    product = repo.get_by_id(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    stats = _feedback_repo.get_summary_stats(product_id, period_days=period_days)

    top_trends = _trends_repo.get_for_product(product_id, limit=1)
    top_trend = top_trends[0]["topic"] if top_trends else None

    last_run = _run_repo.get_last_for_product(product_id)

    return ProductSummaryResponse(
        product_id=product_id,
        product_name=product["name"],
        period=f"last_{period_days}_days",
        total_items=stats["total_items"],
        category_counts=stats["category_counts"],
        avg_sentiment=stats["avg_sentiment"],
        sentiment_trend=stats["sentiment_trend"],
        top_trend=top_trend,
        last_scout_at=last_run["started_at"] if last_run else None,
        last_scout_status=last_run["status"] if last_run else None,
    )
