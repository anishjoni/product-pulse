"""
TrendsRepository — data-access layer for the trends table.

All methods use the get_db() context manager and return plain Python dicts.
category_breakdown is stored as a JSON string in the database and parsed on read.
"""

import json
from typing import Optional

from src.db.database import get_db


class TrendsRepository:
    """Encapsulates all DB operations for the trends domain."""

    def upsert_trends(self, product_id: int, trends: list[dict]) -> None:
        """
        Replace all trend rows for the given product_id with the provided list.

        For each trend dict, the existing row for the same product_id+topic is
        deleted and a fresh row is inserted, so the table always reflects the
        most recent computation without accumulating stale history.

        Expected trend dict keys:
            topic              (str)
            current_count      (int)
            previous_count     (int)
            pct_change         (float)
            category_breakdown (dict)  — stored as JSON
            period_days        (int)
        """
        with get_db() as conn:
            for trend in trends:
                # Remove any existing row for this product+topic combination
                conn.execute(
                    "DELETE FROM trends WHERE product_id = ? AND topic = ?",
                    (product_id, trend["topic"]),
                )
                conn.execute(
                    """
                    INSERT INTO trends
                        (product_id, topic, current_count, previous_count,
                         pct_change, category_breakdown, period_days)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        product_id,
                        trend["topic"],
                        trend["current_count"],
                        trend["previous_count"],
                        trend["pct_change"],
                        json.dumps(trend["category_breakdown"]),
                        trend["period_days"],
                    ),
                )
            conn.commit()

    def get_for_product(self, product_id: int, limit: int = 10) -> list[dict]:
        """
        Return the top N trends for a product, sorted by pct_change DESC.

        category_breakdown is parsed from its JSON string back to a dict.
        """
        with get_db() as conn:
            rows = conn.execute(
                """
                SELECT id, product_id, topic, current_count, previous_count,
                       pct_change, category_breakdown, computed_at, period_days
                FROM trends
                WHERE product_id = ?
                ORDER BY pct_change DESC
                LIMIT ?
                """,
                (product_id, limit),
            ).fetchall()

        result = []
        for row in rows:
            d = dict(row)
            try:
                d["category_breakdown"] = json.loads(d["category_breakdown"])
            except (json.JSONDecodeError, TypeError):
                d["category_breakdown"] = {}
            result.append(d)
        return result

    def get_latest_computed_at(self, product_id: int) -> Optional[str]:
        """
        Return the most recent computed_at timestamp for the given product,
        or None if no trends have been computed yet.
        """
        with get_db() as conn:
            row = conn.execute(
                """
                SELECT computed_at
                FROM trends
                WHERE product_id = ?
                ORDER BY computed_at DESC
                LIMIT 1
                """,
                (product_id,),
            ).fetchone()
        return row["computed_at"] if row else None
