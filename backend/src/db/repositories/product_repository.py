"""
ProductRepository — data-access layer for the products domain.

All methods use the get_db() context manager and return plain Python dicts.
No ORM is used; raw sqlite3 keeps dependencies minimal.
"""

from src.db.database import get_db


def _build_product_dict(row, keywords: list[str], sources: list[dict]) -> dict:
    """Convert a products table row into the canonical product dict."""
    return {
        "id": row["id"],
        "name": row["name"],
        "slug": row["slug"],
        "description": row["description"],
        "is_active": bool(row["is_active"]),
        "created_at": row["created_at"],
        "keywords": keywords,
        "sources": sources,
    }


def _fetch_keywords(conn, product_id: int) -> list[str]:
    rows = conn.execute(
        "SELECT keyword FROM product_keywords WHERE product_id = ? ORDER BY id",
        (product_id,),
    ).fetchall()
    return [r["keyword"] for r in rows]


def _fetch_sources(conn, product_id: int) -> list[dict]:
    rows = conn.execute(
        """
        SELECT source_type, source_ref, is_enabled
        FROM product_sources
        WHERE product_id = ?
        ORDER BY id
        """,
        (product_id,),
    ).fetchall()
    return [
        {
            "source_type": r["source_type"],
            "source_ref": r["source_ref"],
            "is_enabled": bool(r["is_enabled"]),
        }
        for r in rows
    ]


class ProductRepository:
    """Encapsulates all DB operations for the products domain."""

    # ------------------------------------------------------------------
    # Reads
    # ------------------------------------------------------------------

    def get_all_active(self) -> list[dict]:
        """Return all products where is_active = 1, each with nested keywords and sources."""
        with get_db() as conn:
            rows = conn.execute(
                "SELECT * FROM products WHERE is_active = 1 ORDER BY id"
            ).fetchall()
            result = []
            for row in rows:
                keywords = _fetch_keywords(conn, row["id"])
                sources = _fetch_sources(conn, row["id"])
                result.append(_build_product_dict(row, keywords, sources))
        return result

    def get_by_id(self, product_id: int) -> dict | None:
        """Return a single product by primary key, or None if not found."""
        with get_db() as conn:
            row = conn.execute(
                "SELECT * FROM products WHERE id = ?", (product_id,)
            ).fetchone()
            if row is None:
                return None
            keywords = _fetch_keywords(conn, row["id"])
            sources = _fetch_sources(conn, row["id"])
        return _build_product_dict(row, keywords, sources)

    def get_by_slug(self, slug: str) -> dict | None:
        """Return a single product by slug, or None if not found."""
        with get_db() as conn:
            row = conn.execute(
                "SELECT * FROM products WHERE slug = ?", (slug,)
            ).fetchone()
            if row is None:
                return None
            keywords = _fetch_keywords(conn, row["id"])
            sources = _fetch_sources(conn, row["id"])
        return _build_product_dict(row, keywords, sources)

    # ------------------------------------------------------------------
    # Writes
    # ------------------------------------------------------------------

    def create(
        self,
        name: str,
        slug: str,
        description: str | None,
        keywords: list[str],
        sources: list[dict],
    ) -> dict:
        """
        Insert a new product together with its keywords and sources in a single
        transaction.  Returns the full product dict.
        """
        with get_db() as conn:
            cursor = conn.execute(
                "INSERT INTO products (name, slug, description) VALUES (?, ?, ?)",
                (name, slug, description),
            )
            product_id = cursor.lastrowid

            for keyword in keywords:
                conn.execute(
                    "INSERT INTO product_keywords (product_id, keyword) VALUES (?, ?)",
                    (product_id, keyword),
                )

            for source in sources:
                conn.execute(
                    """
                    INSERT INTO product_sources (product_id, source_type, source_ref)
                    VALUES (?, ?, ?)
                    """,
                    (product_id, source["source_type"], source["source_ref"]),
                )

            conn.commit()

            # Re-fetch to get the DB-generated created_at and full row
            row = conn.execute(
                "SELECT * FROM products WHERE id = ?", (product_id,)
            ).fetchone()
            fetched_keywords = _fetch_keywords(conn, product_id)
            fetched_sources = _fetch_sources(conn, product_id)

        return _build_product_dict(row, fetched_keywords, fetched_sources)

    def update_keywords(self, product_id: int, keywords: list[str]) -> None:
        """Replace all keywords for a product."""
        with get_db() as conn:
            conn.execute(
                "DELETE FROM product_keywords WHERE product_id = ?", (product_id,)
            )
            for keyword in keywords:
                conn.execute(
                    "INSERT INTO product_keywords (product_id, keyword) VALUES (?, ?)",
                    (product_id, keyword),
                )
            conn.commit()

    def update_sources(self, product_id: int, sources: list[dict]) -> None:
        """Replace all sources for a product."""
        with get_db() as conn:
            conn.execute(
                "DELETE FROM product_sources WHERE product_id = ?", (product_id,)
            )
            for source in sources:
                conn.execute(
                    """
                    INSERT INTO product_sources (product_id, source_type, source_ref)
                    VALUES (?, ?, ?)
                    """,
                    (product_id, source["source_type"], source["source_ref"]),
                )
            conn.commit()

    def soft_delete(self, product_id: int) -> None:
        """Set is_active = 0 for a product (soft delete)."""
        with get_db() as conn:
            conn.execute(
                "UPDATE products SET is_active = 0 WHERE id = ?", (product_id,)
            )
            conn.commit()
