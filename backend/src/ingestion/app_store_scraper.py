"""
AppStoreScraper — fetches reviews from the Apple App Store via the iTunes RSS API.

source_type : apple_app_store
source_ref  : {app_id}:{country}  e.g. 1403491709:ca
              Country defaults to "us" if omitted.

Fetches up to 10 pages × 50 reviews = 500 max per source.
No API key required.
"""

import logging

import httpx

from src.ingestion.models import RawFeedbackItem

logger = logging.getLogger(__name__)

_MAX_PAGES = 10
_BASE_URL = "https://itunes.apple.com/rss/customerreviews/page={page}/id={app_id}/sortBy=mostRecent/json"


def _parse_source_ref(source_ref: str) -> tuple[str, str]:
    """Split 'app_id:country' → (app_id, country). Country defaults to 'us'."""
    parts = source_ref.split(":", 1)
    app_id = parts[0]
    country = parts[1] if len(parts) > 1 else "us"
    return app_id, country


class AppStoreScraper:
    """Fetches App Store reviews for a product's apple_app_store sources."""

    def fetch(self, product: dict) -> list[RawFeedbackItem]:
        sources = [
            s
            for s in product.get("sources", [])
            if s["source_type"] == "apple_app_store" and s["is_enabled"]
        ]

        if not sources:
            logger.info(
                "No enabled apple_app_store sources for product '%s'.", product.get("name")
            )
            return []

        items: list[RawFeedbackItem] = []

        for source in sources:
            app_id, country = _parse_source_ref(source["source_ref"])
            logger.info(
                "Fetching App Store reviews for app '%s' (country=%s).", app_id, country
            )
            source_items = self._fetch_source(app_id, country)
            items.extend(source_items)
            logger.info(
                "App Store '%s': fetched %d reviews.", app_id, len(source_items)
            )

        logger.info(
            "AppStoreScraper collected %d total items for product '%s'.",
            len(items), product.get("name"),
        )
        return items

    def _fetch_source(self, app_id: str, country: str) -> list[RawFeedbackItem]:
        items: list[RawFeedbackItem] = []
        app_url = f"https://apps.apple.com/app/id{app_id}"

        with httpx.Client(timeout=15) as client:
            for page in range(1, _MAX_PAGES + 1):
                url = _BASE_URL.format(page=page, app_id=app_id)
                try:
                    resp = client.get(
                        url,
                        headers={"Accept": "application/json"},
                        follow_redirects=True,
                    )
                    resp.raise_for_status()
                    data = resp.json()
                except Exception as exc:
                    logger.warning(
                        "Failed to fetch App Store page %d for '%s': %s", page, app_id, exc
                    )
                    break

                entries = data.get("feed", {}).get("entry", [])
                if not entries:
                    break

                # First entry is app metadata — skip it
                for entry in entries[1:]:
                    try:
                        external_id = entry["id"]["label"]
                        content = entry["content"]["label"]
                        author = entry["author"]["name"]["label"]
                        score_str = entry.get("im:rating", {}).get("label", "")
                        score = int(score_str) if score_str.isdigit() else None
                    except (KeyError, TypeError):
                        continue

                    if not content:
                        continue

                    items.append(
                        RawFeedbackItem(
                            source="apple_app_store",
                            source_ref=app_id,
                            external_id=external_id,
                            content=content,
                            author=author,
                            url=app_url,
                            score=score,
                        )
                    )

                # If we got fewer entries than expected the feed is exhausted
                if len(entries) <= 1:
                    break

        return items
