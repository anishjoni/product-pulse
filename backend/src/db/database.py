"""
SQLite connection management using Python's built-in sqlite3.
No SQLAlchemy — keeps dependencies lean for this demo.
"""

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

# Read DATABASE_URL from environment; default to sqlite:///./data/pulse.db
DATABASE_URL: str = os.environ.get("DATABASE_URL", "sqlite:///./data/pulse.db")

# Extract the file path from the sqlite URL (strips the "sqlite:///" prefix)
_DB_PATH: str = DATABASE_URL.replace("sqlite:///", "")


def _ensure_data_dir() -> None:
    """Create the data/ directory if it doesn't exist."""
    db_path = Path(_DB_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)


@contextmanager
def get_db():
    """
    Context manager that yields a sqlite3 connection and ensures it is closed
    afterwards regardless of whether an exception occurred.

    Usage:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(...)
    """
    _ensure_data_dir()
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row  # rows accessible as dicts / by column name
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
    finally:
        conn.close()
