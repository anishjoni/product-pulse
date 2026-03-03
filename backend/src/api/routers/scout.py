"""
Scout router — endpoints for triggering and inspecting data-ingestion scout runs.

Routes:
    POST /products/{product_id}/scout        — trigger a manual scout run (202)
    GET  /products/{product_id}/scout-runs   — list recent runs for a product
    GET  /scout-runs/{run_id}                — get a single scout run by ID
"""

import logging

from fastapi import APIRouter, HTTPException

from src.api.schemas.scout_schemas import ScoutRunResponse
from src.db.repositories.product_repository import ProductRepository
from src.db.repositories.scout_run_repository import ScoutRunRepository
from src.ingestion.scout_runner import ScoutRunner

logger = logging.getLogger(__name__)

router = APIRouter()

_product_repo = ProductRepository()
_run_repo = ScoutRunRepository()


@router.post("/products/{product_id}/scout", status_code=202, response_model=ScoutRunResponse)
def trigger_scout(product_id: int):
    """
    Trigger a manual scout run for the given product.
    Returns 202 Accepted with the scout_run dict once the run completes
    (runs synchronously for now; async workers are a Phase 4 concern).
    """
    product = _product_repo.get_by_id(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    if _run_repo.get_running(product_id) is not None:
        raise HTTPException(
            status_code=409,
            detail="A scout run is already in progress for this product",
        )

    try:
        result = ScoutRunner().run(product_id=product_id, triggered_by="manual")
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.error(
            "Scout run failed for product %d: %s", product_id, exc, exc_info=True
        )
        raise HTTPException(
            status_code=500, detail=f"Scout run failed: {exc}"
        )

    return result


@router.get("/products/{product_id}/scout-runs", response_model=list[ScoutRunResponse])
def list_scout_runs(product_id: int, limit: int = 20):
    """Return the most recent scout runs for a product (newest first)."""
    product = _product_repo.get_by_id(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    return _run_repo.list_for_product(product_id=product_id, limit=limit)


@router.get("/scout-runs/{run_id}", response_model=ScoutRunResponse)
def get_scout_run(run_id: int):
    """Return a single scout run by ID, or 404 if not found."""
    run = _run_repo.get_by_id(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Scout run not found")
    return run
