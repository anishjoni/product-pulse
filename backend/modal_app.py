"""
Modal deployment for the Product Pulse backend.

Prerequisites:
    pip install modal
    modal setup          # authenticate
    modal secret create product-pulse-secrets \
        REDDIT_CLIENT_ID=... \
        REDDIT_CLIENT_SECRET=... \
        REDDIT_USER_AGENT="ProductPulse/1.0" \
        YOUTUBE_API_KEY=... \
        GEMINI_API_KEY=... \
        ANTHROPIC_API_KEY=... \
        DATABASE_URL="sqlite:////app/data/pulse.db" \
        CORS_ORIGINS="https://<your-vercel-app>.vercel.app"

Deploy:
    modal deploy backend/modal_app.py

Note on scheduler:
    APScheduler embedded in FastAPI does not run reliably on Modal's
    serverless containers (container may scale to zero between requests).
    Use the modal_scout_all function below instead — it is registered as
    a Modal Cron and runs on the Modal platform independently of HTTP traffic.
    Set DISABLE_SCHEDULER=1 in the secret to suppress the embedded APScheduler.
"""

import modal

# ---------------------------------------------------------------------------
# Image — Python 3.12, all pip dependencies, source code baked in
# ---------------------------------------------------------------------------

image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install_from_requirements("requirements.txt")
    .copy_local_dir("src", "/app/src")
    .env({"PYTHONPATH": "/app", "DISABLE_SCHEDULER": "1"})
)

# Persistent volume for the SQLite database file
db_volume = modal.Volume.from_name("product-pulse-db", create_if_missing=True)

app = modal.App("product-pulse-backend")

# ---------------------------------------------------------------------------
# FastAPI ASGI endpoint
# ---------------------------------------------------------------------------


@app.function(
    image=image,
    secrets=[modal.Secret.from_name("product-pulse-secrets")],
    volumes={"/app/data": db_volume},
    # Keep one container warm to reduce cold-start latency
    keep_warm=1,
)
@modal.asgi_app()
def fastapi_app():
    import sys
    sys.path.insert(0, "/app")
    from src.api.main import app as _app
    return _app


# ---------------------------------------------------------------------------
# Scheduled scout — runs independently of HTTP traffic
# ---------------------------------------------------------------------------


@app.function(
    image=image,
    secrets=[modal.Secret.from_name("product-pulse-secrets")],
    volumes={"/app/data": db_volume},
    schedule=modal.Cron("0 6 * * *"),  # daily at 06:00 UTC
)
def modal_scout_all():
    """Scout all active products on a daily cron schedule."""
    import sys
    sys.path.insert(0, "/app")
    from src.db.init_db import init_db
    from src.db.seed import seed
    from src.db.repositories.product_repository import ProductRepository
    from src.db.repositories.scout_run_repository import ScoutRunRepository
    from src.ingestion.scout_runner import ScoutRunner
    import logging

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    init_db()
    seed()

    products = ProductRepository().get_all_active()
    run_repo = ScoutRunRepository()

    for product in products:
        if run_repo.get_running(product["id"]) is not None:
            logger.info("Skipping product %d — scout already running", product["id"])
            continue
        logger.info("Scouting product %d ('%s')", product["id"], product["name"])
        try:
            ScoutRunner().run(product_id=product["id"], triggered_by="scheduled")
        except Exception:
            logger.exception("Scout failed for product %d", product["id"])
