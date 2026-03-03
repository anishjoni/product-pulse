"""
Seeds the database with default products on first run.
Idempotent — skips any product whose slug already exists.

Run standalone:
    python -m src.db.seed
"""

from src.db.database import get_db


SEED_PRODUCT = {
    "name": "Wealthsimple Trade",
    "slug": "wealthsimple-trade",
    "description": "Canadian commission-free stock trading app by Wealthsimple",
    "keywords": [
        "wealthsimple",
        "wealthsimple trade",
        "ws trade",
        "wstrade",
        "options spreads",
        "DRIP",
        "fractional shares",
        "crypto",
        "TFSA",
        "RRSP",
    ],
    "sources": [
        {"type": "reddit", "ref": "wealthsimple"},
        {"type": "reddit", "ref": "PersonalFinanceCanada"},
        {"type": "reddit", "ref": "CanadianInvestor"},
        {"type": "youtube", "ref": "wealthsimple trade review"},
        {"type": "youtube", "ref": "wealthsimple trade tutorial"},
    ],
}

SEED_PRODUCT_XBOX = {
    "name": "Xbox",
    "slug": "xbox",
    "description": "Microsoft Xbox gaming platform",
    "keywords": [
        "xbox",
        "xbox series x",
        "gamepass",
        "game pass",
        "phil spencer",
        "matt booty",
        "microsoft gaming",
        "xbox exclusives",
    ],
    "sources": [
        {"type": "reddit", "ref": "xbox"},
        {"type": "reddit", "ref": "XboxSeriesX"},
        {"type": "reddit", "ref": "gaming"},
        {"type": "youtube", "ref": "xbox new ceo 2025"},
        {"type": "youtube", "ref": "xbox game pass 2025"},
    ],
}


def _insert_product(conn, product: dict) -> None:
    """Insert a single product with its keywords and sources if it does not exist."""
    slug = product["slug"]

    # Idempotency check — skip if slug already present
    row = conn.execute(
        "SELECT id FROM products WHERE slug = ?", (slug,)
    ).fetchone()
    if row is not None:
        print(f"  Skipping '{slug}' — already exists.")
        return

    cursor = conn.execute(
        """
        INSERT INTO products (name, slug, description)
        VALUES (?, ?, ?)
        """,
        (product["name"], slug, product.get("description")),
    )
    product_id = cursor.lastrowid

    for keyword in product["keywords"]:
        conn.execute(
            "INSERT INTO product_keywords (product_id, keyword) VALUES (?, ?)",
            (product_id, keyword),
        )

    for source in product["sources"]:
        conn.execute(
            """
            INSERT INTO product_sources (product_id, source_type, source_ref)
            VALUES (?, ?, ?)
            """,
            (product_id, source["type"], source["ref"]),
        )

    print(f"  Inserted '{slug}'.")


def seed() -> None:
    """Insert seed products if they do not already exist."""
    with get_db() as conn:
        for product in (SEED_PRODUCT, SEED_PRODUCT_XBOX):
            _insert_product(conn, product)
        conn.commit()
    print("Seeding complete.")


if __name__ == "__main__":
    seed()
