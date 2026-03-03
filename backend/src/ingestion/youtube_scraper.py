"""
YouTubeScraper — fetches video comments from YouTube Data API v3.

Credentials are read from environment variables (never hard-coded):
    YOUTUBE_API_KEY

API unit cost reference:
    search.list        = 100 units per call
    commentThreads.list =   1 unit per call
"""

import logging
import os

from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from src.ingestion.models import RawFeedbackItem

load_dotenv()

logger = logging.getLogger(__name__)

_MAX_VIDEOS_PER_SEARCH = 5


class YouTubeScraper:
    """Fetches YouTube comments for a product's YouTube sources."""

    def __init__(self) -> None:
        self.youtube = build(
            "youtube",
            "v3",
            developerKey=os.environ["YOUTUBE_API_KEY"],
        )

    def fetch(self, product: dict, limit: int = 20) -> list[RawFeedbackItem]:
        """
        For each enabled youtube source in product["sources"]:
          1. Search YouTube for the source_ref term (costs 100 units per search).
          2. Take the top 5 video results.
          3. For each video: fetch up to `limit` comments (costs 1 unit per call).
          4. Return all comment items as a flat list.

        If the YouTube API returns an error (e.g. quota exceeded), logs a warning
        and returns an empty list — does not crash.
        """
        youtube_sources = [
            s
            for s in product.get("sources", [])
            if s["source_type"] == "youtube" and s["is_enabled"]
        ]

        if not youtube_sources:
            logger.info(
                "No enabled youtube sources for product '%s'.", product.get("name")
            )
            return []

        items: list[RawFeedbackItem] = []
        total_search_units = 0
        total_comment_units = 0

        for source in youtube_sources:
            search_term: str = source["source_ref"]
            logger.info(
                "Searching YouTube for '%s' (product: '%s')",
                search_term,
                product.get("name"),
            )

            # --- Step 1: Search for videos (100 units) ---
            try:
                search_response = (
                    self.youtube.search()
                    .list(
                        q=search_term,
                        part="id,snippet",
                        type="video",
                        maxResults=_MAX_VIDEOS_PER_SEARCH,
                    )
                    .execute()
                )
                total_search_units += 100
            except HttpError as exc:
                logger.warning(
                    "YouTube search failed for '%s': %s", search_term, exc
                )
                continue
            except Exception as exc:
                logger.warning(
                    "Unexpected error during YouTube search for '%s': %s",
                    search_term,
                    exc,
                )
                continue

            video_ids = [
                item["id"]["videoId"]
                for item in search_response.get("items", [])
                if item.get("id", {}).get("kind") == "youtube#video"
            ]

            logger.info(
                "YouTube search for '%s' returned %d video(s).",
                search_term,
                len(video_ids),
            )

            # --- Step 2: Fetch comments for each video (1 unit each) ---
            for video_id in video_ids:
                try:
                    comments_response = (
                        self.youtube.commentThreads()
                        .list(
                            videoId=video_id,
                            part="snippet",
                            maxResults=limit,
                            order="relevance",
                            textFormat="plainText",
                        )
                        .execute()
                    )
                    total_comment_units += 1
                except HttpError as exc:
                    # Comments may be disabled on some videos — log and skip
                    logger.warning(
                        "Could not fetch comments for video %s: %s", video_id, exc
                    )
                    continue
                except Exception as exc:
                    logger.warning(
                        "Unexpected error fetching comments for video %s: %s",
                        video_id,
                        exc,
                    )
                    continue

                for thread in comments_response.get("items", []):
                    snippet = thread.get("snippet", {})
                    top_comment = snippet.get("topLevelComment", {}).get(
                        "snippet", {}
                    )

                    comment_id: str = thread.get("id", "")
                    content: str = top_comment.get("textDisplay", "").strip()
                    if not content:
                        continue

                    items.append(
                        RawFeedbackItem(
                            source="youtube",
                            source_ref=video_id,
                            external_id=comment_id,
                            content=content,
                            author=top_comment.get("authorDisplayName"),
                            url=f"https://youtube.com/watch?v={video_id}&lc={comment_id}",
                            score=top_comment.get("likeCount"),
                        )
                    )

        # Log API unit consumption for this run
        total_units = total_search_units + total_comment_units
        logger.info(
            "YouTube API units consumed: search=%d, comments=%d, total=%d",
            total_search_units,
            total_comment_units,
            total_units,
        )
        logger.info(
            "YouTubeScraper collected %d total items for product '%s'.",
            len(items),
            product.get("name"),
        )
        return items
