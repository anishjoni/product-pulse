from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import insights, reviews, stats

app = FastAPI(title="WS Community Intelligence API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET", "PATCH"],
    allow_headers=["*"],
)

app.include_router(stats.router)
app.include_router(insights.router)
app.include_router(reviews.router)
