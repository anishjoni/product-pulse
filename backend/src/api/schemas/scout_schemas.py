"""
Pydantic schemas for the scout API endpoints.
"""

from pydantic import BaseModel


class ScoutRunResponse(BaseModel):
    """Response schema for a scout_run record."""

    id: int
    product_id: int
    triggered_by: str
    started_at: str
    completed_at: str | None
    status: str
    items_fetched: int
    items_classified: int
    error_message: str | None
