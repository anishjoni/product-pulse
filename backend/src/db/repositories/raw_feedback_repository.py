"""
RawFeedbackRepository — data-access layer for the raw_feedback table.

All methods use the get_db() context manager and return plain Python dicts.
"""

import sqlite3

from src.db.database import get_db
from src.ingestion.models import RawFeedbackItem


def _row_to_dict(row) -> dict:
    """Convert a sqlite3.Row to a plain dict."""
    return dict(row)


class RawFeedbackRepository:
    """Encapsulates all DB operations for the raw_feedback domain."""

    def insert(
        self,
        item: RawFeedbackItem,
        product_id: int,
        scout_run_id: int,
    ) -> bool:
        """
        Insert one RawFeedbackItem.
        Returns True if inserted, False if duplicate (IntegrityError silently swallowed).
        """
        with get_db() as conn:
            try:
                conn.execute(
                    """
                    INSERT INTO raw_feedback
                        (product_id, source, source_ref, external_id,
                         content, author, url, score, scout_run_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        product_id,
                        item.source,
                        item.source_ref,
                        item.external_id,
                        item.content,
                        item.author,
                        item.url,
                        item.score,
                        scout_run_id,
                    ),
                )
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                # UNIQUE(source, external_id) violation — already seen, skip silently
                return False

    def insert_many(
        self,
        items: list[RawFeedbackItem],
        product_id: int,
        scout_run_id: int,
    ) -> int:
        """
        Insert a batch of RawFeedbackItems.
        Returns the count of items actually inserted (duplicates are silently skipped).
        """
        inserted = 0
        for item in items:
            if self.insert(item, product_id, scout_run_id):
                inserted += 1
        return inserted

    def get_unclassified(
        self,
        product_id: int,
        scout_run_id: int,
    ) -> list[dict]:
        """
        Return raw_feedback rows for this product/run that have no corresponding
        classified_feedback row (Phase 3 table).  Falls back to returning all rows
        for the run if the classified_feedback table does not yet exist.
        """
        with get_db() as conn:
            # Check whether classified_feedback table exists yet (Phase 3 creates it)
            table_exists = conn.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='classified_feedback'
                """
            ).fetchone()

            if table_exists:
                rows = conn.execute(
                    """
                    SELECT rf.*
                    FROM raw_feedback rf
                    LEFT JOIN classified_feedback cf ON cf.raw_feedback_id = rf.id
                    WHERE rf.product_id = ?
                      AND rf.scout_run_id = ?
                      AND cf.id IS NULL
                    ORDER BY rf.id
                    """,
                    (product_id, scout_run_id),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT * FROM raw_feedback
                    WHERE product_id = ?
                      AND scout_run_id = ?
                    ORDER BY id
                    """,
                    (product_id, scout_run_id),
                ).fetchall()
        return [_row_to_dict(r) for r in rows]

    def count_for_run(self, scout_run_id: int) -> int:
        """Return the total number of raw_feedback rows for a given scout_run_id."""
        with get_db() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS cnt FROM raw_feedback WHERE scout_run_id = ?",
                (scout_run_id,),
            ).fetchone()
        return row["cnt"]
