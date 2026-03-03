"""
FastAPI application entry point for Product Pulse.
"""

import logging
import os
from datetime import datetime, timezone

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routers import feedback as feedback_router
from src.api.routers import products as products_router
from src.api.routers import scout as scout_router
from src.api.routers import trends as trends_router
from src.db.init_db import init_db
from src.db.repositories.product_repository import ProductRepository
from src.db.repositories.scout_run_repository import ScoutRunRepository
from src.db.seed import seed
from src.ingestion.scout_runner import ScoutRunner

logger = logging.getLogger(__name__)

app = FastAPI(title="Product Pulse API", version="0.1.0")

# ---------------------------------------------------------------------------
# CORS — allow all origins for development; restrict via CORS_ORIGINS in prod
# ---------------------------------------------------------------------------
cors_origins_env = os.environ.get("CORS_ORIGINS", "*")
cors_origins = (
    [o.strip() for o in cors_origins_env.split(",")]
    if cors_origins_env != "*"
    else ["*"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

scheduler = AsyncIOScheduler()


def _run_scout_for_product(product_id: int) -> None:
    """Run a scout for one product (called from scheduler thread pool)."""
    run_repo = ScoutRunRepository()
    if run_repo.get_running(product_id) is not None:
        logger.info("Skipping scheduled scout for product %d — already running", product_id)
        return
    try:
        ScoutRunner().run(product_id=product_id, triggered_by="scheduled")
        logger.info("Scheduled scout completed for product %d", product_id)
    except Exception:
        logger.exception("Scheduled scout failed for product %d", product_id)


def scheduled_scout_all() -> None:
    """Trigger a scout run for every active product. Called by APScheduler."""
    products = ProductRepository().get_all_active()
    for product in products:
        _run_scout_for_product(product["id"])


def _check_overdue_and_run() -> None:
    """
    On startup: scout any product that has not been scouted in the last 23 hours.
    Runs synchronously so the first request is not blocked.
    """
    products = ProductRepository().get_all_active()
    run_repo = ScoutRunRepository()
    now = datetime.now(tz=timezone.utc)
    for product in products:
        last_run = run_repo.get_last_for_product(product["id"])
        if last_run is None:
            logger.info(
                "Product %d ('%s') has never been scouted — running now",
                product["id"],
                product["name"],
            )
            _run_scout_for_product(product["id"])
            continue

        started_at_str = last_run.get("started_at")
        if started_at_str:
            try:
                last_dt = datetime.fromisoformat(started_at_str).replace(tzinfo=timezone.utc)
                hours_since = (now - last_dt).total_seconds() / 3600
                if hours_since > 23:
                    logger.info(
                        "Product %d ('%s') last scouted %.1f h ago — running now",
                        product["id"],
                        product["name"],
                        hours_since,
                    )
                    _run_scout_for_product(product["id"])
            except ValueError:
                logger.warning("Could not parse started_at '%s' for product %d", started_at_str, product["id"])


# ---------------------------------------------------------------------------
# Startup / shutdown
# ---------------------------------------------------------------------------


@app.on_event("startup")
async def on_startup() -> None:
    """Initialise DB tables, seed default products, and start the scheduler."""
    init_db()
    seed()

    # DISABLE_SCHEDULER=1 is set by modal_app.py — Modal runs its own cron function
    if os.environ.get("DISABLE_SCHEDULER") == "1":
        logger.info("Scheduler disabled via DISABLE_SCHEDULER env var (Modal mode).")
        return

    # Parse cron expression from env (default: daily at 06:00 UTC)
    cron_expr = os.environ.get("SCOUT_SCHEDULE_CRON", "0 6 * * *")
    parts = cron_expr.split()
    if len(parts) == 5:
        trigger = CronTrigger(
            minute=parts[0],
            hour=parts[1],
            day=parts[2],
            month=parts[3],
            day_of_week=parts[4],
            timezone="UTC",
        )
    else:
        logger.warning("Invalid SCOUT_SCHEDULE_CRON '%s'; falling back to 0 6 * * *", cron_expr)
        trigger = CronTrigger(minute=0, hour=6, timezone="UTC")

    scheduler.add_job(scheduled_scout_all, trigger, id="daily_scout", replace_existing=True)
    scheduler.start()
    logger.info("Scheduler started with cron: %s", cron_expr)

    # Catch up any overdue products without blocking startup
    import asyncio
    asyncio.get_event_loop().run_in_executor(None, _check_overdue_and_run)


@app.on_event("shutdown")
async def on_shutdown() -> None:
    """Shut down the APScheduler gracefully."""
    scheduler.shutdown(wait=False)


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(products_router.router, prefix="")
app.include_router(scout_router.router, prefix="")
app.include_router(trends_router.router, prefix="")
app.include_router(feedback_router.router, prefix="")

# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


@app.get("/health")
def health_check():
    """Simple liveness probe."""
    return {"status": "ok"}
