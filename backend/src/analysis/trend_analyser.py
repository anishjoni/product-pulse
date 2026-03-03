"""
TrendAnalyser — computes trending topics for a product using Polars.

Algorithm (per scout run):
  1. Load classified_feedback joined to raw_feedback for the last 2*period_days.
  2. Parse LLM-extracted topics JSON arrays and explode into one row per topic.
  3. Normalise topics: lowercase, strip punctuation, filter stop words, min length 3.
  4. Split into current window (0 → period_days ago) and previous window
     (period_days → 2*period_days ago).
  5. Count topic occurrences per window using Polars group_by.
  6. Join windows, compute pct_change = (current - previous) / max(previous, 1) * 100.
  7. Filter: current_count >= 3 AND pct_change >= 50.
  8. For each qualifying topic, build a category_breakdown dict.
  9. Upsert results into the trends table.
  10. Return sorted list of trend dicts.

Polars is used for all aggregation — no pandas, no Python loops over rows.
"""

import json
import logging
import re
from datetime import datetime, timedelta

import polars as pl

from src.analysis.stop_words import STOP_WORDS
from src.db.database import get_db
from src.db.repositories.trends_repository import TrendsRepository

logger = logging.getLogger(__name__)

# Minimum mentions in current window for a topic to qualify as a trend.
MIN_CURRENT_COUNT = 3

# Minimum percentage increase over the previous window to qualify.
MIN_PCT_CHANGE = 50.0


def _normalise(topic: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace."""
    topic = topic.lower().strip()
    topic = re.sub(r"[^a-z0-9 ]", "", topic)
    return topic.strip()


class TrendAnalyser:
    """Computes trending topics for a product and stores results in the DB."""

    def __init__(self) -> None:
        self._trends_repo = TrendsRepository()

    def compute_trends(self, product_id: int, period_days: int = 7) -> list[dict]:
        """
        Compute trends for the given product over the specified period.

        Returns a list of trend dicts sorted by pct_change DESC.
        Each dict has keys:
            topic, current_count, previous_count, pct_change,
            category_breakdown, period_days
        """
        now = datetime.utcnow()
        cutoff_date = now - timedelta(days=2 * period_days)
        current_start = now - timedelta(days=period_days)

        # ------------------------------------------------------------------
        # 1. Load data from SQLite
        # ------------------------------------------------------------------
        with get_db() as conn:
            rows = conn.execute(
                """
                SELECT
                    cf.id,
                    cf.category,
                    cf.topics        AS topics_json,
                    cf.classified_at,
                    rf.content,
                    rf.product_id
                FROM classified_feedback cf
                JOIN raw_feedback rf ON cf.raw_feedback_id = rf.id
                WHERE rf.product_id = ?
                  AND cf.classification_status = 'success'
                  AND cf.classified_at >= ?
                """,
                (product_id, cutoff_date.isoformat()),
            ).fetchall()

            # Also load product keywords for keyword-presence tracking
            kw_rows = conn.execute(
                "SELECT keyword FROM product_keywords WHERE product_id = ?",
                (product_id,),
            ).fetchall()

        keywords = [r["keyword"].lower() for r in kw_rows]

        if not rows:
            logger.info(
                "TrendAnalyser: no classified feedback found for product %d "
                "in the last %d days. Returning empty trends.",
                product_id,
                2 * period_days,
            )
            return []

        # ------------------------------------------------------------------
        # 2. Build base Polars DataFrame
        # ------------------------------------------------------------------
        df = pl.DataFrame(
            [dict(r) for r in rows],
            schema={
                "id": pl.Int64,
                "category": pl.Utf8,
                "topics_json": pl.Utf8,
                "classified_at": pl.Utf8,
                "content": pl.Utf8,
                "product_id": pl.Int64,
            },
        )

        # ------------------------------------------------------------------
        # 3. Parse topics JSON → explode into one row per topic
        # ------------------------------------------------------------------
        df = df.with_columns(
            pl.col("topics_json")
            .map_elements(
                lambda x: json.loads(x) if x else [],
                return_dtype=pl.List(pl.Utf8),
            )
            .alias("topics_list")
        )

        # ------------------------------------------------------------------
        # 4. Also inject product keywords that appear in raw content
        # ------------------------------------------------------------------
        # For each row, check which product keywords appear in the content
        # and append them to the topics_list.
        if keywords:

            def _add_keyword_topics(row_content: str) -> list[str]:
                content_lower = row_content.lower() if row_content else ""
                return [kw for kw in keywords if kw in content_lower]

            df = df.with_columns(
                pl.col("content")
                .map_elements(_add_keyword_topics, return_dtype=pl.List(pl.Utf8))
                .alias("kw_topics")
            ).with_columns(
                pl.concat_list(["topics_list", "kw_topics"]).alias("topics_list")
            )

        # Explode: one row per topic
        df = (
            df.explode("topics_list")
            .rename({"topics_list": "topic"})
            .drop("topics_json", "content")
        )

        # Drop rows where topic is null or empty after explode
        df = df.filter(pl.col("topic").is_not_null() & (pl.col("topic") != ""))

        # ------------------------------------------------------------------
        # 5. Normalise topics
        # ------------------------------------------------------------------
        df = df.with_columns(
            pl.col("topic")
            .map_elements(_normalise, return_dtype=pl.Utf8)
            .alias("topic")
        ).filter(
            (pl.col("topic").str.len_chars() >= 3)
            & (~pl.col("topic").is_in(list(STOP_WORDS)))
        )

        if df.is_empty():
            logger.info(
                "TrendAnalyser: no topics remain after normalisation for product %d.",
                product_id,
            )
            return []

        # ------------------------------------------------------------------
        # 6. Parse classified_at into a datetime column
        # ------------------------------------------------------------------
        df = df.with_columns(
            pl.col("classified_at")
            .str.strptime(pl.Datetime, "%Y-%m-%dT%H:%M:%S", strict=False)
            .alias("classified_dt")
        )

        # ------------------------------------------------------------------
        # 7. Split into current and previous windows
        # ------------------------------------------------------------------
        current_df = df.filter(pl.col("classified_dt") >= current_start)
        previous_df = df.filter(pl.col("classified_dt") < current_start)

        # ------------------------------------------------------------------
        # 8. Count topic occurrences per window
        # ------------------------------------------------------------------
        current_counts = current_df.group_by("topic").agg(
            pl.len().alias("current_count")
        )
        previous_counts = previous_df.group_by("topic").agg(
            pl.len().alias("previous_count")
        )

        # ------------------------------------------------------------------
        # 9. Join windows and compute pct_change
        # ------------------------------------------------------------------
        merged = (
            current_counts.join(previous_counts, on="topic", how="left")
            .with_columns(pl.col("previous_count").fill_null(0))
            .with_columns(
                (
                    (pl.col("current_count") - pl.col("previous_count"))
                    / pl.col("previous_count").clip(lower_bound=1)
                    * 100
                ).alias("pct_change")
            )
            .filter(
                (pl.col("current_count") >= MIN_CURRENT_COUNT)
                & (pl.col("pct_change") >= MIN_PCT_CHANGE)
            )
            .sort("pct_change", descending=True)
        )

        if merged.is_empty():
            logger.info(
                "TrendAnalyser: no qualifying trends for product %d "
                "(min_count=%d, min_pct=%.0f).",
                product_id,
                MIN_CURRENT_COUNT,
                MIN_PCT_CHANGE,
            )
            return []

        # ------------------------------------------------------------------
        # 10. Category breakdown per qualifying topic
        # ------------------------------------------------------------------
        # Build breakdown from the current window only
        breakdown_df = current_df.group_by(["topic", "category"]).agg(
            pl.len().alias("count")
        )

        qualifying_topics = merged["topic"].to_list()

        # Filter breakdown to only qualifying topics
        breakdown_df = breakdown_df.filter(pl.col("topic").is_in(qualifying_topics))

        # Convert breakdown to a dict keyed by topic for fast lookup
        breakdown_map: dict[str, dict] = {}
        for row in breakdown_df.iter_rows(named=True):
            t = row["topic"]
            if t not in breakdown_map:
                breakdown_map[t] = {}
            breakdown_map[t][row["category"]] = row["count"]

        # ------------------------------------------------------------------
        # 11. Assemble result list
        # ------------------------------------------------------------------
        trends: list[dict] = []
        for row in merged.iter_rows(named=True):
            topic = row["topic"]
            trend = {
                "topic": topic,
                "current_count": int(row["current_count"]),
                "previous_count": int(row["previous_count"]),
                "pct_change": round(float(row["pct_change"]), 2),
                "category_breakdown": breakdown_map.get(topic, {}),
                "period_days": period_days,
            }
            trends.append(trend)

        # ------------------------------------------------------------------
        # 12. Persist to database
        # ------------------------------------------------------------------
        self._trends_repo.upsert_trends(product_id, trends)
        logger.info(
            "TrendAnalyser: upserted %d trends for product %d (period=%d days).",
            len(trends),
            product_id,
            period_days,
        )

        return trends
