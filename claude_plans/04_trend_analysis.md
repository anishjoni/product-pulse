# Phase 4 — Trend Analysis Engine

## Goal
After each scout run, compute which topics are surging in mentions. A trend is meaningful
when both absolute volume AND relative growth are significant — prevents single noisy posts
from appearing as trends.

## Agents Involved
- Backend (implementation)
- Devil's Advocate (validate spike detection logic, edge cases with thin data)

## What is a Trend?

A topic qualifies as a trend when, comparing the current 7-day window to the previous 7-day window:
- Absolute mentions in current window: ≥ 3 (avoids 1→3 looking like 200%)
- Percentage increase: ≥ 50%
- Not a stop word or common English word (filter list applied)

Formula:
```
pct_change = ((current_count - previous_count) / max(previous_count, 1)) * 100
```

## Data Model

```sql
CREATE TABLE trends (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id      INTEGER NOT NULL REFERENCES products(id),
    topic           TEXT NOT NULL,              -- e.g. "options spreads"
    current_count   INTEGER NOT NULL,           -- mentions in last 7 days
    previous_count  INTEGER NOT NULL,           -- mentions in prior 7 days
    pct_change      REAL NOT NULL,              -- percentage change
    category_breakdown TEXT NOT NULL,           -- JSON: {"feature_request": 5, "complaint": 2}
    computed_at     TEXT NOT NULL DEFAULT (datetime('now')),
    period_days     INTEGER NOT NULL DEFAULT 7
);
```

## Topic Extraction

Topics come from two sources, merged and deduplicated:
1. `classified_feedback.topics` — LLM-extracted keywords per item
2. Product keywords that appear in `raw_feedback.content` — ensures product-specific terms always tracked

Normalisation before counting:
- Lowercase all topics
- Strip punctuation
- Deduplicate ("Options Spreads" and "options spreads" are the same)
- Filter stop words: ["the", "a", "is", "in", "it", "of", "to", "and", "for", "with", "that", "this"]

## TrendAnalyser Class

```python
class TrendAnalyser:
    def compute_trends(self, product_id: int) -> list[TrendResult]:
        """
        1. Load all classified_feedback for product within last 14 days
        2. Split into current window (days 0-7) and previous window (days 7-14)
        3. Count topic occurrences in each window using Polars groupby
        4. Compute pct_change for each topic
        5. Filter: current_count >= 3 AND pct_change >= 50
        6. For each qualifying topic, compute category_breakdown
        7. Upsert into trends table (replace existing record for same product+topic+date)
        8. Return sorted by pct_change DESC
        """
```

## Using Polars for Efficiency

```python
import polars as pl

# Load data into Polars DataFrame
df = pl.DataFrame(classified_items)

# Explode topics array per item
df_exploded = df.explode("topics")

# Split into windows
current = df_exploded.filter(pl.col("age_days") <= 7)
previous = df_exploded.filter((pl.col("age_days") > 7) & (pl.col("age_days") <= 14))

# Count per topic
current_counts = current.group_by("topic").agg(pl.len().alias("current_count"))
previous_counts = previous.group_by("topic").agg(pl.len().alias("previous_count"))

# Join and compute pct_change
trends = current_counts.join(previous_counts, on="topic", how="left").with_columns(
    pct_change = ((pl.col("current_count") - pl.col("previous_count").fill_null(0))
                  / pl.col("previous_count").fill_null(1).clip(lower_bound=1) * 100)
)
```

## API Output (for frontend bar chart)

```json
{
  "trends": [
    {
      "topic": "options spreads",
      "current_count": 24,
      "previous_count": 8,
      "pct_change": 200.0,
      "category_breakdown": {
        "feature_request": 18,
        "complaint": 4,
        "general_discussion": 2
      }
    },
    ...
  ],
  "computed_at": "2025-01-15T09:00:00Z",
  "period_days": 7
}
```

## File Structure
```
src/
  analysis/
    __init__.py
    trend_analyser.py
    stop_words.py       # STOP_WORDS set
  db/
    repositories/
      trends_repository.py
```

## Acceptance Criteria
- [ ] A topic with 1 mention in previous window and 2 in current does NOT appear (below min count)
- [ ] A topic with 8 mentions previous and 24 current appears with pct_change = 200.0
- [ ] Stop words ("the", "is", "a") never appear in trends output
- [ ] category_breakdown sums to current_count
- [ ] Trends are recomputed after every scout run completes
- [ ] With zero historical data (first run), trends are returned with pct_change based on 0 previous
- [ ] Polars is used for all aggregation (no pandas, no pure Python loops over large lists)
