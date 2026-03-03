"""
ClassifiedFeedbackRepository — data-access layer for the classified_feedback table.

All methods use the get_db() context manager and return plain Python dicts.
Topics are stored as JSON strings in the database and deserialized on read.
"""

import json

from src.db.database import get_db


def _row_to_dict(row) -> dict:
    """Convert a sqlite3.Row to a plain dict."""
    return dict(row)


class ClassifiedFeedbackRepository:
    """Encapsulates all DB operations for the classified_feedback domain."""

    def insert(
        self,
        raw_feedback_id: int,
        category: str,
        sentiment: float,
        summary: str,
        topics: list[str],
        confidence: float,
        llm_provider: str,
    ) -> None:
        """
        Insert a successfully classified feedback row.
        topics is stored as a JSON array string in the database.
        """
        with get_db() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO classified_feedback
                    (raw_feedback_id, category, sentiment, summary,
                     topics, confidence, llm_provider, classification_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'success')
                """,
                (
                    raw_feedback_id,
                    category,
                    sentiment,
                    summary,
                    json.dumps(topics),
                    confidence,
                    llm_provider,
                ),
            )
            conn.commit()

    def insert_failed(self, raw_feedback_id: int, llm_provider: str) -> None:
        """
        Insert a placeholder row for a failed classification.
        Uses default/zero values so the item is not lost; can be retried later.
        """
        with get_db() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO classified_feedback
                    (raw_feedback_id, category, sentiment, summary,
                     topics, confidence, llm_provider, classification_status)
                VALUES (?, 'general_discussion', 0, '', '[]', 0, ?, 'failed')
                """,
                (raw_feedback_id, llm_provider),
            )
            conn.commit()

    def get_for_run(self, scout_run_id: int) -> list[dict]:
        """
        Return all classified_feedback rows for the given scout_run_id.
        Joins classified_feedback with raw_feedback to filter by scout_run_id.
        topics is deserialized from JSON back to a Python list.
        """
        with get_db() as conn:
            rows = conn.execute(
                """
                SELECT cf.*
                FROM classified_feedback cf
                JOIN raw_feedback rf ON rf.id = cf.raw_feedback_id
                WHERE rf.scout_run_id = ?
                ORDER BY cf.id
                """,
                (scout_run_id,),
            ).fetchall()
        result = []
        for row in rows:
            d = _row_to_dict(row)
            try:
                d["topics"] = json.loads(d["topics"])
            except (json.JSONDecodeError, TypeError):
                d["topics"] = []
            result.append(d)
        return result

    def count_for_product(self, product_id: int) -> dict:
        """
        Return counts of classified_feedback rows grouped by category for a product.
        Example: {"feature_request": 12, "bug_report": 5, "complaint": 3, ...}
        """
        with get_db() as conn:
            rows = conn.execute(
                """
                SELECT cf.category, COUNT(*) AS cnt
                FROM classified_feedback cf
                JOIN raw_feedback rf ON rf.id = cf.raw_feedback_id
                WHERE rf.product_id = ?
                  AND cf.classification_status = 'success'
                GROUP BY cf.category
                """,
                (product_id,),
            ).fetchall()
        return {row["category"]: row["cnt"] for row in rows}

    def get_paginated(
        self,
        product_id: int,
        page: int = 1,
        page_size: int = 20,
        category: str | None = None,
        source: str | None = None,
        sentiment: str | None = None,
        search: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> tuple[list[dict], int]:
        """
        Return a page of classified feedback for a product with optional filters.
        Also returns the total matching row count for pagination metadata.

        sentiment values: "positive" (>0.3), "negative" (<-0.3), "neutral" (between)
        search performs case-insensitive substring match on raw content and summary.
        Returns (items, total).
        """
        where = ["rf.product_id = ?", "cf.classification_status = 'success'"]
        params: list = [product_id]

        if category:
            where.append("cf.category = ?")
            params.append(category)
        if source:
            where.append("rf.source = ?")
            params.append(source)
        if sentiment == "positive":
            where.append("cf.sentiment > 0.3")
        elif sentiment == "negative":
            where.append("cf.sentiment < -0.3")
        elif sentiment == "neutral":
            where.append("cf.sentiment BETWEEN -0.3 AND 0.3")
        if search:
            where.append("(LOWER(rf.content) LIKE ? OR LOWER(cf.summary) LIKE ?)")
            like = f"%{search.lower()}%"
            params.extend([like, like])
        if date_from:
            where.append("rf.fetched_at >= ?")
            params.append(date_from)
        if date_to:
            where.append("rf.fetched_at <= ?")
            params.append(date_to)

        where_sql = " AND ".join(where)
        join_sql = "JOIN raw_feedback rf ON rf.id = cf.raw_feedback_id"

        count_sql = (
            f"SELECT COUNT(*) AS cnt FROM classified_feedback cf {join_sql} WHERE {where_sql}"
        )
        data_sql = f"""
            SELECT cf.id, cf.raw_feedback_id, cf.category, cf.sentiment,
                   cf.summary, cf.topics, cf.confidence, cf.llm_provider,
                   cf.classified_at, rf.source, rf.source_ref, rf.external_id,
                   rf.author, rf.url, rf.score, rf.fetched_at
            FROM classified_feedback cf {join_sql}
            WHERE {where_sql}
            ORDER BY rf.fetched_at DESC
            LIMIT ? OFFSET ?
        """
        offset = (page - 1) * page_size

        with get_db() as conn:
            total = conn.execute(count_sql, params).fetchone()["cnt"]
            rows = conn.execute(data_sql, params + [page_size, offset]).fetchall()

        items = []
        for row in rows:
            d = _row_to_dict(row)
            try:
                d["topics"] = json.loads(d["topics"])
            except (json.JSONDecodeError, TypeError):
                d["topics"] = []
            items.append(d)
        return items, total

    def get_by_id(self, feedback_id: int) -> dict | None:
        """
        Return a single classified feedback item by its primary key.
        Includes the raw content field for detail views.
        Returns None if not found.
        """
        with get_db() as conn:
            row = conn.execute(
                """
                SELECT cf.id, cf.raw_feedback_id, cf.category, cf.sentiment,
                       cf.summary, cf.topics, cf.confidence, cf.llm_provider,
                       cf.classified_at, cf.classification_status,
                       rf.source, rf.source_ref, rf.external_id, rf.content,
                       rf.author, rf.url, rf.score, rf.fetched_at, rf.product_id
                FROM classified_feedback cf
                JOIN raw_feedback rf ON rf.id = cf.raw_feedback_id
                WHERE cf.id = ?
                """,
                (feedback_id,),
            ).fetchone()
        if row is None:
            return None
        d = _row_to_dict(row)
        try:
            d["topics"] = json.loads(d["topics"])
        except (json.JSONDecodeError, TypeError):
            d["topics"] = []
        return d

    def get_summary_stats(self, product_id: int, period_days: int = 7) -> dict:
        """
        Return aggregate stats for the summary endpoint.
        Includes category counts and avg sentiment for the current and previous period.
        """
        with get_db() as conn:
            # Category counts for current period
            cat_rows = conn.execute(
                """
                SELECT cf.category, COUNT(*) AS cnt
                FROM classified_feedback cf
                JOIN raw_feedback rf ON rf.id = cf.raw_feedback_id
                WHERE rf.product_id = ?
                  AND cf.classification_status = 'success'
                  AND rf.fetched_at >= datetime('now', ?)
                GROUP BY cf.category
                """,
                (product_id, f"-{period_days} days"),
            ).fetchall()

            total_row = conn.execute(
                """
                SELECT COUNT(*) AS cnt
                FROM classified_feedback cf
                JOIN raw_feedback rf ON rf.id = cf.raw_feedback_id
                WHERE rf.product_id = ?
                  AND cf.classification_status = 'success'
                  AND rf.fetched_at >= datetime('now', ?)
                """,
                (product_id, f"-{period_days} days"),
            ).fetchone()

            # Avg sentiment: current period
            cur_sent = conn.execute(
                """
                SELECT AVG(cf.sentiment) AS avg_s
                FROM classified_feedback cf
                JOIN raw_feedback rf ON rf.id = cf.raw_feedback_id
                WHERE rf.product_id = ?
                  AND cf.classification_status = 'success'
                  AND rf.fetched_at >= datetime('now', ?)
                """,
                (product_id, f"-{period_days} days"),
            ).fetchone()

            # Avg sentiment: previous period (for trend direction)
            prev_sent = conn.execute(
                """
                SELECT AVG(cf.sentiment) AS avg_s
                FROM classified_feedback cf
                JOIN raw_feedback rf ON rf.id = cf.raw_feedback_id
                WHERE rf.product_id = ?
                  AND cf.classification_status = 'success'
                  AND rf.fetched_at >= datetime('now', ?)
                  AND rf.fetched_at < datetime('now', ?)
                """,
                (product_id, f"-{period_days * 2} days", f"-{period_days} days"),
            ).fetchone()

        category_counts = {row["category"]: row["cnt"] for row in cat_rows}
        total = total_row["cnt"] if total_row else 0
        avg_sentiment = cur_sent["avg_s"] if cur_sent and cur_sent["avg_s"] is not None else 0.0
        prev_avg = prev_sent["avg_s"] if prev_sent and prev_sent["avg_s"] is not None else None

        if prev_avg is None or abs(avg_sentiment - prev_avg) < 0.05:
            sentiment_trend = "stable"
        elif avg_sentiment > prev_avg:
            sentiment_trend = "improving"
        else:
            sentiment_trend = "declining"

        return {
            "total_items": total,
            "category_counts": category_counts,
            "avg_sentiment": round(avg_sentiment, 4),
            "sentiment_trend": sentiment_trend,
        }
