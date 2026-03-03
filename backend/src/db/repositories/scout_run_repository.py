"""
ScoutRunRepository — data-access layer for the scout_runs table.

All methods use the get_db() context manager and return plain Python dicts.
"""

from src.db.database import get_db


def _row_to_dict(row) -> dict:
    """Convert a sqlite3.Row to a plain dict."""
    return dict(row)


class ScoutRunRepository:
    """Encapsulates all DB operations for the scout_runs domain."""

    def create(self, product_id: int, triggered_by: str = "manual") -> dict:
        """
        Insert a new scout_run with status 'running'.
        Returns the newly-created row as a dict.
        """
        with get_db() as conn:
            cursor = conn.execute(
                """
                INSERT INTO scout_runs (product_id, triggered_by, status)
                VALUES (?, ?, 'running')
                """,
                (product_id, triggered_by),
            )
            run_id = cursor.lastrowid
            conn.commit()
            row = conn.execute(
                "SELECT * FROM scout_runs WHERE id = ?", (run_id,)
            ).fetchone()
        return _row_to_dict(row)

    def complete(self, run_id: int, items_fetched: int) -> None:
        """Mark a scout_run as completed and record how many items were fetched."""
        with get_db() as conn:
            conn.execute(
                """
                UPDATE scout_runs
                SET status = 'completed',
                    completed_at = datetime('now'),
                    items_fetched = ?
                WHERE id = ?
                """,
                (items_fetched, run_id),
            )
            conn.commit()

    def fail(self, run_id: int, error_message: str) -> None:
        """Mark a scout_run as failed and store the error message."""
        with get_db() as conn:
            conn.execute(
                """
                UPDATE scout_runs
                SET status = 'failed',
                    completed_at = datetime('now'),
                    error_message = ?
                WHERE id = ?
                """,
                (error_message, run_id),
            )
            conn.commit()

    def update_classified(self, run_id: int, items_classified: int) -> None:
        """Update the items_classified count for a scout_run."""
        with get_db() as conn:
            conn.execute(
                "UPDATE scout_runs SET items_classified = ? WHERE id = ?",
                (items_classified, run_id),
            )
            conn.commit()

    def get_by_id(self, run_id: int) -> dict | None:
        """Return a single scout_run by primary key, or None if not found."""
        with get_db() as conn:
            row = conn.execute(
                "SELECT * FROM scout_runs WHERE id = ?", (run_id,)
            ).fetchone()
        if row is None:
            return None
        return _row_to_dict(row)

    def list_for_product(self, product_id: int, limit: int = 20) -> list[dict]:
        """Return the most recent scout_runs for a product (newest first)."""
        with get_db() as conn:
            rows = conn.execute(
                """
                SELECT * FROM scout_runs
                WHERE product_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (product_id, limit),
            ).fetchall()
        return [_row_to_dict(r) for r in rows]

    def get_running(self, product_id: int) -> dict | None:
        """Return the currently-running scout run for a product, or None."""
        with get_db() as conn:
            row = conn.execute(
                """
                SELECT * FROM scout_runs
                WHERE product_id = ? AND status = 'running'
                ORDER BY id DESC
                LIMIT 1
                """,
                (product_id,),
            ).fetchone()
        return _row_to_dict(row) if row else None

    def get_last_for_product(self, product_id: int) -> dict | None:
        """Return the most recent scout run for a product regardless of status, or None."""
        with get_db() as conn:
            row = conn.execute(
                """
                SELECT * FROM scout_runs
                WHERE product_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (product_id,),
            ).fetchone()
        return _row_to_dict(row) if row else None
