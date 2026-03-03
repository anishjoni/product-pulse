# Phase 2 — Data Ingestion

## Goal
Build scrapers for Reddit and YouTube that fetch recent posts/comments for a configured product,
apply rate limiting to control costs, and store raw results before any LLM processing.

## Agents Involved
- Backend (implementation)
- QA (validate rate limiter, validate schema compliance)

## Sources

### Reddit (via PRAW)
- Auth: Reddit API app credentials (free, just requires account + app registration)
- Fetch: New posts from each configured subreddit, filtered by product keywords
- Per run limit: 15–20 posts per subreddit (configurable via `SCOUT_POST_LIMIT` env var)
- Include: post title + selftext, top-level comments (up to 10 per post), post score, URL

### YouTube (via YouTube Data API v3)
- Auth: Google API key (free tier: 10,000 units/day — a search costs 100 units)
- Fetch: Search results for configured search terms, then fetch comments for top 5 videos
- Per run limit: 5 videos × 20 comments = 100 items per search term
- Include: video title, comment text, comment like count, video URL, published_at

### Twitter/X — Phase 2 Only
- Minimum viable access requires Basic tier ($100/month) — out of scope for demo
- Schema is designed to accept twitter source_type for future compatibility
- No implementation in Phase 1

## Data Model

```sql
CREATE TABLE raw_feedback (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id   INTEGER NOT NULL REFERENCES products(id),
    source       TEXT NOT NULL,          -- "reddit" | "youtube" | "twitter"
    source_ref   TEXT NOT NULL,          -- subreddit name or YouTube video ID
    external_id  TEXT NOT NULL,          -- Reddit post/comment ID or YouTube comment ID
    content      TEXT NOT NULL,          -- full text of post/comment
    author       TEXT,
    url          TEXT,
    score        INTEGER,                -- upvotes (Reddit) or likes (YouTube)
    fetched_at   TEXT NOT NULL DEFAULT (datetime('now')),
    scout_run_id INTEGER REFERENCES scout_runs(id),
    UNIQUE(source, external_id)          -- prevent duplicate ingestion
);

CREATE TABLE scout_runs (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id   INTEGER NOT NULL REFERENCES products(id),
    triggered_by TEXT NOT NULL DEFAULT 'scheduled',  -- "scheduled" | "manual"
    started_at   TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at TEXT,
    status       TEXT NOT NULL DEFAULT 'running',    -- "running" | "completed" | "failed"
    items_fetched INTEGER DEFAULT 0,
    items_classified INTEGER DEFAULT 0,
    error_message TEXT
);
```

## Implementation

### File Structure
```
src/
  ingestion/
    __init__.py
    reddit_scraper.py       # RedditScraper class
    youtube_scraper.py      # YouTubeScraper class
    scout_runner.py         # orchestrates a full scout run for one product
  db/
    repositories/
      raw_feedback_repository.py
      scout_run_repository.py
```

### RedditScraper
```python
class RedditScraper:
    def fetch(self, product: Product, limit: int = 15) -> list[RawFeedbackItem]:
        """
        For each enabled reddit source in product:
          - Search subreddit for posts containing any product keyword
          - Fetch up to `limit` posts sorted by new
          - For each post, fetch top 10 comments
          - Return deduplicated list of RawFeedbackItem
        """
```

### YouTubeScraper
```python
class YouTubeScraper:
    def fetch(self, product: Product, limit: int = 20) -> list[RawFeedbackItem]:
        """
        For each enabled youtube source in product:
          - Search YouTube for the source_ref term
          - Take top 5 video results
          - Fetch up to `limit` comments per video
          - Return deduplicated list of RawFeedbackItem
        """
```

### Rate Limiting Rules
- Reddit: 1 request per 2 seconds (PRAW handles OAuth throttling automatically)
- YouTube: Respect 10,000 unit/day quota. Log unit consumption per run.
- Both: Skip items already in `raw_feedback` (check `UNIQUE(source, external_id)`)

### RawFeedbackItem (dataclass)
```python
@dataclass
class RawFeedbackItem:
    source: str
    source_ref: str
    external_id: str
    content: str
    author: str | None
    url: str | None
    score: int | None
```

## Environment Variables Required
```
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
REDDIT_USER_AGENT=ProductPulse/1.0
YOUTUBE_API_KEY=
SCOUT_POST_LIMIT=15   # max posts per subreddit per run
```

## Acceptance Criteria
- [ ] RedditScraper fetches ≤ SCOUT_POST_LIMIT posts per subreddit per run
- [ ] YouTubeScraper fetches comments for top 5 videos per search term
- [ ] Duplicate external_ids are silently skipped (UNIQUE constraint)
- [ ] Scout run record is created with status "running" before fetch starts
- [ ] Scout run record is updated to "completed" or "failed" when done
- [ ] All fetched items written to raw_feedback table with correct product_id
- [ ] Running a second scout does not re-insert already-seen items
