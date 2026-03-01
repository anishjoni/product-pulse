from fastapi import APIRouter

import api.data as data_module
from api.models import Review, ReviewUpdate

router = APIRouter()


@router.get("/api/reviews", response_model=list[Review])
def list_reviews() -> list[Review]:
    return data_module.load_review_log(data_module.DEFAULT_DATA_DIR)


@router.patch("/api/reviews/{insight_id}", response_model=Review)
def update_review(insight_id: str, update: ReviewUpdate) -> Review:
    return data_module.save_review(insight_id, update, data_module.DEFAULT_DATA_DIR)
