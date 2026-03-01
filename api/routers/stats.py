from fastapi import APIRouter

import api.data as data_module
from api.models import Stats

router = APIRouter()


@router.get("/api/stats", response_model=Stats)
def get_stats() -> Stats:
    insights = data_module.load_insights(data_module.DEFAULT_DATA_DIR)
    reviews = data_module.load_review_log(data_module.DEFAULT_DATA_DIR)
    reviewed_ids = {r.insight_id for r in reviews if r.status != "pending"}
    return Stats(
        total_posts=sum(i.post_count for i in insights),
        total_insights=len(insights),
        pending_review=sum(1 for i in insights if i.id not in reviewed_ids),
        flagged_for_review=sum(1 for i in insights if i.needs_human_review),
    )
