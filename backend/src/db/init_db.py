"""
Creates all database tables.
Idempotent — safe to run on every application start.

Run standalone:
    python -m src.db.init_db
"""

from src.db.database import get_db


CREATE_PRODUCTS = """
CREATE TABLE IF NOT EXISTS products (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL UNIQUE,
    slug        TEXT NOT NULL UNIQUE,
    description TEXT,
    is_active   INTEGER NOT NULL DEFAULT 1,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

CREATE_PRODUCT_KEYWORDS = """
CREATE TABLE IF NOT EXISTS product_keywords (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id  INTEGER NOT NULL REFERENCES products(id),
    keyword     TEXT NOT NULL,
    weight      REAL NOT NULL DEFAULT 1.0
);
"""

CREATE_PRODUCT_SOURCES = """
CREATE TABLE IF NOT EXISTS product_sources (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id  INTEGER NOT NULL REFERENCES products(id),
    source_type TEXT NOT NULL,
    source_ref  TEXT NOT NULL,
    is_enabled  INTEGER NOT NULL DEFAULT 1
);
"""

# scout_runs must be created before raw_feedback because raw_feedback references it.
CREATE_SCOUT_RUNS = """
CREATE TABLE IF NOT EXISTS scout_runs (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id       INTEGER NOT NULL REFERENCES products(id),
    triggered_by     TEXT NOT NULL DEFAULT 'scheduled',
    started_at       TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at     TEXT,
    status           TEXT NOT NULL DEFAULT 'running',
    items_fetched    INTEGER DEFAULT 0,
    items_classified INTEGER DEFAULT 0,
    error_message    TEXT
);
"""

CREATE_RAW_FEEDBACK = """
CREATE TABLE IF NOT EXISTS raw_feedback (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id   INTEGER NOT NULL REFERENCES products(id),
    source       TEXT NOT NULL,
    source_ref   TEXT NOT NULL,
    external_id  TEXT NOT NULL,
    content      TEXT NOT NULL,
    author       TEXT,
    url          TEXT,
    score        INTEGER,
    fetched_at   TEXT NOT NULL DEFAULT (datetime('now')),
    scout_run_id INTEGER REFERENCES scout_runs(id),
    UNIQUE(source, external_id)
);
"""

CREATE_CLASSIFIED_FEEDBACK = """
CREATE TABLE IF NOT EXISTS classified_feedback (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    raw_feedback_id       INTEGER NOT NULL UNIQUE REFERENCES raw_feedback(id),
    category              TEXT NOT NULL,
    sentiment             REAL NOT NULL,
    summary               TEXT NOT NULL,
    topics                TEXT NOT NULL,
    confidence            REAL NOT NULL,
    llm_provider          TEXT NOT NULL,
    classified_at         TEXT NOT NULL DEFAULT (datetime('now')),
    classification_status TEXT NOT NULL DEFAULT 'success'
);
"""

CREATE_TRENDS = """
CREATE TABLE IF NOT EXISTS trends (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id        INTEGER NOT NULL REFERENCES products(id),
    topic             TEXT NOT NULL,
    current_count     INTEGER NOT NULL,
    previous_count    INTEGER NOT NULL,
    pct_change        REAL NOT NULL,
    category_breakdown TEXT NOT NULL,
    computed_at       TEXT NOT NULL DEFAULT (datetime('now')),
    period_days       INTEGER NOT NULL DEFAULT 7
);
"""


def init_db() -> None:
    """Create all tables if they do not already exist."""
    with get_db() as conn:
        conn.execute(CREATE_PRODUCTS)
        conn.execute(CREATE_PRODUCT_KEYWORDS)
        conn.execute(CREATE_PRODUCT_SOURCES)
        conn.execute(CREATE_SCOUT_RUNS)
        conn.execute(CREATE_RAW_FEEDBACK)
        conn.execute(CREATE_CLASSIFIED_FEEDBACK)
        conn.execute(CREATE_TRENDS)
        conn.commit()
    print("Database tables created (or already exist).")


if __name__ == "__main__":
    init_db()
