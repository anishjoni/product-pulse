"""
Reddit data collector using PRAW.
Collects posts and comments from Wealthsimple-relevant subreddits.

Setup:
    1. Create a Reddit app at https://www.reddit.com/prefs/apps (script type)
    2. Add credentials to .env (see .env.example)
    3. Read-only mode works without credentials but has lower rate limits

Usage:
    uv run python pipeline/collect_reddit.py
"""

import time

import polars as pl
import praw
from tqdm import tqdm

from pipeline.config import (
    RAW_DIR,
    WEALTHSIMPLE_KEYWORDS,
    logger,
    optional_env,
)

SUBREDDITS = ["PersonalFinanceCanada", "wealthsimple", "CanadianInvestor"]


def build_reddit_client() -> praw.Reddit:
    client_id = optional_env("REDDIT_CLIENT_ID")
    client_secret = optional_env("REDDIT_CLIENT_SECRET")
    user_agent = optional_env("REDDIT_USER_AGENT", "WealthsimpleCommunityIntel/1.0")

    if client_id and client_secret:
        logger.info("Using authenticated Reddit client")
        return praw.Reddit(client_id=client_id, client_secret=client_secret, user_agent=user_agent)

    logger.warning("No Reddit credentials — using read-only mode (lower rate limits)")
    return praw.Reddit(client_id="placeholder", client_secret="placeholder", user_agent=user_agent)


def _is_ws_relevant(text: str) -> bool:
    t = text.lower()
    return any(kw in t for kw in WEALTHSIMPLE_KEYWORDS)


def collect_subreddit(
    reddit: praw.Reddit,
    subreddit_name: str,
    limit: int = 500,
    time_filter: str = "year",
) -> list[dict]:
    records = []
    subreddit = reddit.subreddit(subreddit_name)
    is_ws_sub = subreddit_name.lower() == "wealthsimple"

    logger.info(f"Collecting r/{subreddit_name} (limit={limit}, time_filter={time_filter})")
    try:
        posts = list(subreddit.top(time_filter=time_filter, limit=limit))
    except Exception as e:
        logger.error(f"Failed to fetch r/{subreddit_name}: {e}")
        return records

    for post in tqdm(posts, desc=f"r/{subreddit_name}"):
        combined = f"{post.title} {post.selftext}"
        if not is_ws_sub and not _is_ws_relevant(combined):
            continue

        records.append(
            {
                "id": post.id,
                "source": "reddit",
                "subreddit": subreddit_name,
                "type": "post",
                "title": post.title,
                "text": post.selftext,
                "url": f"https://reddit.com{post.permalink}",
                "score": post.score,
                "num_comments": post.num_comments,
                "rating": None,
                "created_utc": str(post.created_utc),
                "author": str(post.author) if post.author else "[deleted]",
            }
        )

        try:
            post.comments.replace_more(limit=0)
            for comment in post.comments[:20]:
                if not comment.body or comment.body in ("[deleted]", "[removed]"):
                    continue
                records.append(
                    {
                        "id": comment.id,
                        "source": "reddit",
                        "subreddit": subreddit_name,
                        "type": "comment",
                        "title": post.title,
                        "text": comment.body,
                        "url": f"https://reddit.com{comment.permalink}",
                        "score": comment.score,
                        "num_comments": 0,
                        "rating": None,
                        "created_utc": str(comment.created_utc),
                        "author": str(comment.author) if comment.author else "[deleted]",
                    }
                )
        except Exception as e:
            logger.debug(f"Could not fetch comments for {post.id}: {e}")

    logger.info(f"Collected {len(records)} records from r/{subreddit_name}")
    return records


def collect_search(
    reddit: praw.Reddit,
    subreddit_name: str,
    query: str = "wealthsimple",
    limit: int = 200,
) -> list[dict]:
    records = []
    logger.info(f"Searching r/{subreddit_name} for '{query}'")
    try:
        for post in reddit.subreddit(subreddit_name).search(
            query, sort="relevance", time_filter="year", limit=limit
        ):
            records.append(
                {
                    "id": post.id,
                    "source": "reddit",
                    "subreddit": subreddit_name,
                    "type": "post_search",
                    "title": post.title,
                    "text": post.selftext,
                    "url": f"https://reddit.com{post.permalink}",
                    "score": post.score,
                    "num_comments": post.num_comments,
                    "rating": None,
                    "created_utc": str(post.created_utc),
                    "author": str(post.author) if post.author else "[deleted]",
                }
            )
    except Exception as e:
        logger.error(f"Search failed in r/{subreddit_name}: {e}")

    logger.info(f"Found {len(records)} search results in r/{subreddit_name}")
    return records


def run() -> pl.DataFrame:
    reddit = build_reddit_client()
    all_records: list[dict] = []

    for sub in SUBREDDITS:
        all_records.extend(collect_subreddit(reddit, sub, limit=500, time_filter="year"))
        time.sleep(1)

    for sub in ["PersonalFinanceCanada", "CanadianInvestor"]:
        all_records.extend(collect_search(reddit, sub, query="wealthsimple", limit=200))
        time.sleep(1)

    df = pl.DataFrame(all_records).unique(subset=["id"])
    logger.success(f"Total unique Reddit records: {len(df)}")

    output_path = RAW_DIR / "reddit_raw.ndjson"
    df.write_ndjson(output_path)
    logger.info(f"Saved → {output_path}")
    return df


if __name__ == "__main__":
    df = run()
    print(f"\nCollected {len(df)} Reddit records")
    print(df.group_by(["subreddit", "type"]).len().sort("len", descending=True))
