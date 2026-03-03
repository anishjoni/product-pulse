"""
GooglePlayScraper — fetches reviews from the Google Play Store.

source_type : google_play
source_ref  : {app_id}:{country}  e.g. com.wealthsimple.trade:ca
              Country defaults to "us" if omitted.

Env vars:
    SCOUT_REVIEW_LIMIT   (default: 100)
"""

import logging
import os

from google_play_scraper import Sort, reviews

from src.ingestion.models import RawFeedbackItem

logger = logging.getLogger(__name__)


def _parse_source_ref(source_ref: str) -> tuple[str, str]:
    """Split 'app_id:country' → (app_id, country). Country defaults to 'us'."""
    parts = source_ref.split(":", 1)
    app_id = parts[0]
    country = parts[1] if len(parts) > 1 else "us"
    return app_id, country


class GooglePlayScraper:
    """Fetches Play Store reviews for a product's google_play sources."""

    def fetch(self, product: dict, limit: int = None) -> list[RawFeedbackItem]:
        if limit is None:
            limit = int(os.environ.get("SCOUT_REVIEW_LIMIT", 100))

        sources = [
            s
            for s in product.get("sources", [])
            if s["source_type"] == "google_play" and s["is_enabled"]
        ]

        if not sources:
            logger.info(
                "No enabled google_play sources for product '%s'.", product.get("name")
            )
            return []

        items: list[RawFeedbackItem] = []

        for source in sources:
            app_id, country = _parse_source_ref(source["source_ref"])
            logger.info(
                "Fetching Play Store reviews for app '%s' (country=%s, limit=%d).",
                app_id, country, limit,
            )
            try:
                result, _ = reviews(
                    app_id,
                    lang="en",
                    country=country,
                    sort=Sort.NEWEST,
                    count=limit,
                )
            except Exception as exc:
                logger.warning(
                    "Failed to fetch Play Store reviews for '%s': %s", app_id, exc
                )
                continue

            for r in result:
                content = r.get("content") or ""
                if not content:
                    continue
                items.append(
                    RawFeedbackItem(
                        source="google_play",
                        source_ref=app_id,
                        external_id=r["reviewId"],
                        content=content,
                        author=r.get("userName"),
                        url=f"https://play.google.com/store/apps/details?id={app_id}",
                        score=r.get("score"),
                    )
                )

            logger.info(
                "Play Store '%s': fetched %d reviews.", app_id, len(result)
            )

        logger.info(
            "GooglePlayScraper collected %d total items for product '%s'.",
            len(items), product.get("name"),
        )
        return items
