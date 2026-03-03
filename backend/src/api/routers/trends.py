"""
Trends router — endpoint for retrieving computed trending topics.

Routes:
    GET /products/{product_id}/trends   — return trending topics for a product
"""

import logging

from fastapi import APIRouter, HTTPException, Query

from src.analysis.trend_analyser import TrendAnalyser
from src.api.schemas.trends_schemas import TrendItem, TrendsResponse
from src.db.repositories.product_repository import ProductRepository
from src.db.repositories.trends_repository import TrendsRepository

logger = logging.getLogger(__name__)

router = APIRouter()

_product_repo = ProductRepository()
_trends_repo = TrendsRepository()


@router.get(
    "/products/{product_id}/trends",
    response_model=TrendsResponse,
    summary="Get trending topics for a product",
)
def get_trends(
    product_id: int,
    period_days: int = Query(default=7, ge=1, le=90, description="Window size in days"),
    limit: int = Query(default=10, ge=1, le=100, description="Max topics to return"),
    recompute: bool = Query(
        default=False,
        description="If true, recompute trends on-demand before returning",
    ),
):
    """
    Return trending topics for the given product.

    Trends are normally computed at the end of each scout run. Pass
    `recompute=true` to trigger a fresh computation synchronously.

    Response is sorted by pct_change DESC.
    """
    product = _product_repo.get_by_id(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    if recompute:
        try:
            analyser = TrendAnalyser()
            analyser.compute_trends(product_id=product_id, period_days=period_days)
        except Exception as exc:
            logger.error(
                "On-demand trend computation failed for product %d: %s",
                product_id,
                exc,
                exc_info=True,
            )
            raise HTTPException(
                status_code=500,
                detail=f"Trend computation failed: {exc}",
            )

    raw_trends = _trends_repo.get_for_product(product_id=product_id, limit=limit)
    computed_at = _trends_repo.get_latest_computed_at(product_id)

    trend_items = [
        TrendItem(
            topic=t["topic"],
            current_count=t["current_count"],
            previous_count=t["previous_count"],
            pct_change=t["pct_change"],
            category_breakdown=t["category_breakdown"],
        )
        for t in raw_trends
    ]

    return TrendsResponse(
        product_id=product_id,
        trends=trend_items,
        computed_at=computed_at,
        period_days=period_days,
    )
