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
        {"type": "google_play", "ref": "com.wealthsimple.trade:ca"},
        {"type": "apple_app_store", "ref": "1403491709:ca"},
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
        {"type": "google_play", "ref": "com.microsoft.xboxone.smartglass:us"},
        {"type": "apple_app_store", "ref": "736179781:us"},
    ],
}


def _insert_product(conn, product: dict) -> None:
    """Insert a single product with its keywords and sources if it does not exist.

    Source seeding always runs with an existence check so new sources can be
    added to an already-seeded product without duplicating existing rows.
    """
    slug = product["slug"]

    row = conn.execute(
        "SELECT id FROM products WHERE slug = ?", (slug,)
    ).fetchone()

    if row is None:
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
        print(f"  Inserted '{slug}'.")
    else:
        product_id = row[0]
        print(f"  Product '{slug}' already exists (id={product_id}), checking sources…")

    # Always seed sources — skip any that already exist
    for source in product["sources"]:
        existing = conn.execute(
            "SELECT id FROM product_sources WHERE product_id=? AND source_type=? AND source_ref=?",
            (product_id, source["type"], source["ref"]),
        ).fetchone()
        if existing is None:
            conn.execute(
                """
                INSERT INTO product_sources (product_id, source_type, source_ref)
                VALUES (?, ?, ?)
                """,
                (product_id, source["type"], source["ref"]),
            )
            print(f"    + Added source {source['type']}:{source['ref']}")


def seed() -> None:
    """Insert seed products if they do not already exist."""
    with get_db() as conn:
        for product in (SEED_PRODUCT, SEED_PRODUCT_XBOX):
            _insert_product(conn, product)
        conn.commit()
    print("Seeding complete.")


if __name__ == "__main__":
    seed()
