# Phase 5 — REST API Layer

## Goal
Expose all backend functionality via a FastAPI application that the Next.js frontend consumes.
Also hosts the APScheduler for scheduled scout runs.

## Agents Involved
- Backend (implementation)
- QA (validate all endpoints return correct shape, test error cases)

## Base URL
- Local: `http://localhost:8000`
- Modal: `https://<app>.modal.run`

## Endpoints

### Products
```
GET    /products                    List all active products
POST   /products                    Create a new product (with keywords + sources)
GET    /products/{id}               Get product details
PUT    /products/{id}               Update product (keywords, sources, name)
DELETE /products/{id}               Soft delete (set is_active = 0)
```

### Scout Runs
```
POST   /products/{id}/scout         Trigger a manual scout run (async, returns run_id)
GET    /products/{id}/scout-runs    List past scout runs for a product
GET    /scout-runs/{run_id}         Get status + stats for a specific run
```

### Feedback
```
GET    /products/{id}/feedback      Paginated classified feedback feed
  Query params:
    page=1, page_size=20
    category=feature_request|bug_report|complaint|praise|general_discussion
    source=reddit|youtube
    sentiment=positive|negative|neutral   (positive > 0.3, negative < -0.3)
    search=<text>                          full-text search on content/summary
    date_from=YYYY-MM-DD
    date_to=YYYY-MM-DD

GET    /feedback/{id}               Full detail for one feedback item (includes raw content)
```

### Trends
```
GET    /products/{id}/trends        Current trends for a product
  Query params:
    period_days=7    (default 7, max 30)
    limit=20         (top N trends)
```

### Dashboard Summary
```
GET    /products/{id}/summary       Pulse overview for the dashboard header
```
Response shape:
```json
{
  "product_id": 1,
  "product_name": "Wealthsimple Trade",
  "period": "last_7_days",
  "total_items": 312,
  "category_counts": {
    "feature_request": 87,
    "bug_report": 45,
    "complaint": 63,
    "praise": 71,
    "general_discussion": 46
  },
  "avg_sentiment": -0.12,
  "sentiment_trend": "declining",   // "improving" | "declining" | "stable"
  "top_trend": "options spreads",
  "last_scout_at": "2025-01-15T06:00:00Z",
  "last_scout_status": "completed"
}
```

## Scheduling
- APScheduler embedded in FastAPI startup
- Default: scout all active products daily at 06:00 UTC
- Schedule configurable via `SCOUT_SCHEDULE_CRON` env var (default: `0 6 * * *`)
- On app start: check if any product hasn't been scouted in > 23 hours → run immediately

## CORS
- Allow all origins in development (`*`)
- Lock down to frontend domain in production

## File Structure
```
src/
  api/
    __init__.py
    main.py             # FastAPI app, lifespan (scheduler setup), CORS
    routers/
      products.py
      feedback.py
      trends.py
      scout.py
    schemas/            # Pydantic request/response models
      product_schemas.py
      feedback_schemas.py
      trend_schemas.py
```

## Environment Variables
```
DATABASE_URL=sqlite:///./pulse.db        # or postgresql://...
SCOUT_SCHEDULE_CRON=0 6 * * *
CORS_ORIGINS=http://localhost:3000
```

## Error Handling Convention
- 404: resource not found → `{"detail": "Product not found"}`
- 422: validation error → FastAPI default
- 500: unexpected error → `{"detail": "Internal error", "error_id": "<uuid>"}` (log full trace)
- Scout already running: 409 → `{"detail": "A scout run is already in progress for this product"}`

## Acceptance Criteria
- [ ] `GET /products` returns seeded Wealthsimple Trade product
- [ ] `POST /products/{id}/scout` returns 202 with run_id, scout runs in background
- [ ] `GET /products/{id}/feedback?category=feature_request` returns only feature requests
- [ ] `GET /products/{id}/trends` returns topics sorted by pct_change DESC
- [ ] `GET /products/{id}/summary` returns correct category counts matching DB
- [ ] Scheduler triggers scout at configured cron time without manual intervention
- [ ] Second call to `POST /scout` while one is running returns 409
