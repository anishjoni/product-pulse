"""
RedditScraper — fetches posts and comments from configured subreddits via PRAW.

Credentials are read from environment variables (never hard-coded):
    REDDIT_CLIENT_ID
    REDDIT_CLIENT_SECRET
    REDDIT_USER_AGENT    (default: "ProductPulse/1.0")
    SCOUT_POST_LIMIT     (default: 15)
"""

import logging
import os

import praw
from dotenv import load_dotenv

from src.ingestion.models import RawFeedbackItem

load_dotenv()

logger = logging.getLogger(__name__)


class RedditScraper:
    """Fetches Reddit posts and top-level comments for a product's subreddit sources."""

    def __init__(self) -> None:
        self.reddit = praw.Reddit(
            client_id=os.environ["REDDIT_CLIENT_ID"],
            client_secret=os.environ["REDDIT_CLIENT_SECRET"],
            user_agent=os.environ.get("REDDIT_USER_AGENT", "ProductPulse/1.0"),
        )

    def fetch(self, product: dict, limit: int = None) -> list[RawFeedbackItem]:
        """
        For each enabled reddit source in product["sources"]:
          1. Get subreddit by source_ref name.
          2. Search for posts containing any product keyword (OR query, first 5 keywords).
          3. Fetch up to `limit` posts sorted by "new".
          4. For each post: create a RawFeedbackItem from title + selftext.
          5. Also fetch top 10 comments per post (skip deleted/removed).
          6. Return all items as a flat list.

        Posts with score < 0 are skipped (likely noise).
        """
        if limit is None:
            limit = int(os.environ.get("SCOUT_POST_LIMIT", 15))

        reddit_sources = [
            s
            for s in product.get("sources", [])
            if s["source_type"] == "reddit" and s["is_enabled"]
        ]

        if not reddit_sources:
            logger.info(
                "No enabled reddit sources for product '%s'.", product.get("name")
            )
            return []

        # Build keyword search query — limit to first 5 to keep query short
        keywords: list[str] = product.get("keywords", [])[:5]
        query = " OR ".join(keywords) if keywords else product.get("name", "")

        items: list[RawFeedbackItem] = []

        for source in reddit_sources:
            subreddit_name: str = source["source_ref"]
            logger.info(
                "Fetching r/%s for product '%s' (query: %s, limit: %d)",
                subreddit_name,
                product.get("name"),
                query,
                limit,
            )

            try:
                subreddit = self.reddit.subreddit(subreddit_name)
                posts = list(subreddit.search(query, sort="new", limit=limit))
            except Exception as exc:
                logger.warning(
                    "Failed to fetch r/%s: %s", subreddit_name, exc
                )
                continue

            logger.info(
                "r/%s returned %d posts.", subreddit_name, len(posts)
            )

            for post in posts:
                # Skip heavily downvoted posts
                if post.score < 0:
                    logger.debug("Skipping post %s (score=%d)", post.id, post.score)
                    continue

                # Build post content: title + selftext (if any)
                selftext = post.selftext.strip()
                content = (
                    f"{post.title}\n\n{selftext}" if selftext else post.title
                )

                items.append(
                    RawFeedbackItem(
                        source="reddit",
                        source_ref=subreddit_name,
                        external_id=f"post_{post.id}",
                        content=content,
                        author=str(post.author) if post.author else None,
                        url=f"https://reddit.com{post.permalink}",
                        score=post.score,
                    )
                )

                # Fetch top 10 comments for this post
                try:
                    post.comments.replace_more(limit=0)  # don't follow "load more" links
                    top_comments = post.comments.list()[:10]
                except Exception as exc:
                    logger.warning(
                        "Failed to fetch comments for post %s: %s", post.id, exc
                    )
                    top_comments = []

                for comment in top_comments:
                    body: str = getattr(comment, "body", "") or ""
                    if body in ("[deleted]", "[removed]", ""):
                        continue

                    items.append(
                        RawFeedbackItem(
                            source="reddit",
                            source_ref=subreddit_name,
                            external_id=f"comment_{comment.id}",
                            content=body,
                            author=(
                                str(comment.author)
                                if comment.author
                                else None
                            ),
                            url=f"https://reddit.com{post.permalink}",
                            score=comment.score,
                        )
                    )

        logger.info(
            "RedditScraper collected %d total items for product '%s'.",
            len(items),
            product.get("name"),
        )
        return items
