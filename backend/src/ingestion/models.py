"""
Data models for the ingestion pipeline.
"""

from dataclasses import dataclass


@dataclass
class RawFeedbackItem:
    source: str        # "reddit" | "youtube"
    source_ref: str    # subreddit name or YouTube video ID
    external_id: str   # Reddit post/comment ID or YouTube comment ID
    content: str       # full text
    author: str | None
    url: str | None
    score: int | None  # upvotes or likes
