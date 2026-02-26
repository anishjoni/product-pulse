"""
App Store and Google Play review collector for the Wealthsimple app.

Usage:
    uv run python pipeline/collect_appstore.py
"""

import polars as pl

from pipeline.config import RAW_DIR, logger

GOOGLE_PLAY_APP_ID = "com.wealthsimple.trade"
APP_STORE_APP_ID = "1057997402"
APP_STORE_COUNTRY = "ca"


def collect_google_play(app_id: str, count: int = 2000) -> list[dict]:
    try:
        from google_play_scraper import Sort, reviews
    except ImportError:
        logger.error("google-play-scraper not installed — run: uv sync")
        return []

    logger.info(f"Collecting Google Play reviews for {app_id}")
    records = []
    try:
        result, _ = reviews(app_id, lang="en", country="ca", sort=Sort.NEWEST, count=count)
        for r in result:
            records.append(
                {
                    "id": f"gplay_{r['reviewId']}",
                    "source": "google_play",
                    "subreddit": None,
                    "type": "review",
                    "title": None,
                    "text": r.get("content", ""),
                    "url": f"https://play.google.com/store/apps/details?id={app_id}",
                    "score": r.get("thumbsUpCount", 0),
                    "num_comments": 0,
                    "rating": float(r["score"]) if r.get("score") else None,
                    "created_utc": r["at"].isoformat() if r.get("at") else None,
                    "author": r.get("userName", "anonymous"),
                }
            )
    except Exception as e:
        logger.error(f"Google Play collection failed: {e}")

    logger.info(f"Collected {len(records)} Google Play reviews")
    return records


def collect_app_store(app_id: str, country: str = "ca", count: int = 2000) -> list[dict]:
    try:
        from app_store_web_scraper import AppStoreEntry
    except ImportError:
        logger.error("app-store-web-scraper not installed — run: uv sync")
        return []

    logger.info(f"Collecting App Store reviews for app_id={app_id}")
    records = []
    try:
        app = AppStoreEntry(app_id=app_id, country=country)

        for r in app.reviews(limit=count):
            records.append(
                {
                    "id": f"appstore_{r.id}",
                    "source": "app_store",
                    "subreddit": None,
                    "type": "review",
                    "title": r.title or "",
                    "text": r.content or "",
                    "url": f"https://apps.apple.com/{country}/app/id{app_id}",
                    "score": 0,
                    "num_comments": 0,
                    "rating": float(r.rating) if r.rating is not None else None,
                    "created_utc": r.date.isoformat() if r.date else None,
                    "author": r.user_name or "anonymous",
                }
            )
    except Exception as e:
        logger.error(f"App Store collection failed: {e}")

    logger.info(f"Collected {len(records)} App Store reviews")
    return records


def run() -> pl.DataFrame:
    all_records = collect_google_play(GOOGLE_PLAY_APP_ID, count=2000)
    all_records.extend(collect_app_store(APP_STORE_APP_ID, country=APP_STORE_COUNTRY, count=2000))

    if not all_records:
        logger.warning("No records collected from app stores.")
        return pl.DataFrame()

    df = (
        pl.DataFrame(all_records)
        .unique(subset=["id"])
        .filter(pl.col("text").str.strip_chars().str.len_chars() > 10)
    )
    logger.success(f"Total app store records: {len(df)}")

    output_path = RAW_DIR / "appstore_raw.ndjson"
    df.write_ndjson(output_path)
    logger.info(f"Saved → {output_path}")
    return df


if __name__ == "__main__":
    df = run()
    if not df.is_empty():
        print(f"\nCollected {len(df)} app store records")
        print(df.group_by("source").len())
        avg_rating = df.filter(pl.col("rating").is_not_null())["rating"].mean()
        print(f"Avg rating: {avg_rating:.2f}")
