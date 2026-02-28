from fastapi import APIRouter, HTTPException, Query

import api.data as data_module
from api.models import Insight

router = APIRouter()


@router.get("/api/insights", response_model=list[Insight])
def list_insights(
    category: str | None = Query(None),
    confidence: str | None = Query(None),
    flagged: bool | None = Query(None),
) -> list[Insight]:
    items = data_module.load_insights(data_module.DEFAULT_DATA_DIR)
    if category:
        items = [i for i in items if i.category == category]
    if confidence:
        items = [i for i in items if i.confidence == confidence]
    if flagged is not None:
        items = [i for i in items if i.needs_human_review == flagged]
    return items


@router.get("/api/insights/{insight_id}", response_model=Insight)
def get_insight(insight_id: str) -> Insight:
    match = next(
        (i for i in data_module.load_insights(data_module.DEFAULT_DATA_DIR) if i.id == insight_id),
        None,
    )
    if not match:
        raise HTTPException(status_code=404, detail="Insight not found")
    return match
