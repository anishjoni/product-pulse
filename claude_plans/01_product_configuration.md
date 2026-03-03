# Phase 1 — Product Configuration

## Goal
Allow the system to be configured for any target product. All scraping, classification, and
trend analysis is scoped to a product. The demo should ship with one pre-seeded product
("Wealthsimple Trade") but the system must support adding more without code changes.

## Agents Involved
- Backend (implementation)
- QA (validate seed data loads correctly)

## Data Model

```sql
CREATE TABLE products (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL UNIQUE,          -- "Wealthsimple Trade"
    slug        TEXT NOT NULL UNIQUE,          -- "wealthsimple-trade"
    description TEXT,
    is_active   INTEGER NOT NULL DEFAULT 1,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE product_keywords (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id  INTEGER NOT NULL REFERENCES products(id),
    keyword     TEXT NOT NULL,                 -- "wealthsimple", "options spreads", "DRIP"
    weight      REAL NOT NULL DEFAULT 1.0      -- higher = more important for trend scoring
);

CREATE TABLE product_sources (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id  INTEGER NOT NULL REFERENCES products(id),
    source_type TEXT NOT NULL,                 -- "reddit" | "youtube" | "twitter"
    source_ref  TEXT NOT NULL,                 -- subreddit name | channel ID | search term
    is_enabled  INTEGER NOT NULL DEFAULT 1
);
```

## Seed Data (Wealthsimple Trade)

```python
SEED_PRODUCT = {
    "name": "Wealthsimple Trade",
    "slug": "wealthsimple-trade",
    "description": "Canadian commission-free stock trading app by Wealthsimple",
    "keywords": [
        "wealthsimple", "wealthsimple trade", "ws trade", "wstrade",
        "options spreads", "DRIP", "fractional shares", "crypto", "TFSA", "RRSP"
    ],
    "sources": [
        {"type": "reddit", "ref": "wealthsimple"},
        {"type": "reddit", "ref": "PersonalFinanceCanada"},
        {"type": "reddit", "ref": "CanadianInvestor"},
        {"type": "youtube", "ref": "wealthsimple trade review"},
        {"type": "youtube", "ref": "wealthsimple trade tutorial"}
    ]
}

SEED_PRODUCT_XBOX = {
    "name": "Xbox",
    "slug": "xbox",
    "description": "Microsoft Xbox gaming platform",
    "keywords": [
        "xbox", "xbox series x", "gamepass", "game pass", "phil spencer",
        "matt booty", "microsoft gaming", "xbox exclusives"
    ],
    "sources": [
        {"type": "reddit", "ref": "xbox"},
        {"type": "reddit", "ref": "XboxSeriesX"},
        {"type": "reddit", "ref": "gaming"},
        {"type": "youtube", "ref": "xbox new ceo 2025"},
        {"type": "youtube", "ref": "xbox game pass 2025"}
    ]
}
```

## Implementation Notes

- Build a `ProductRepository` class in `src/db/repositories/product_repository.py`
- Expose a `POST /products` endpoint to add new products via API
- Expose a `GET /products` endpoint to list all products
- Expose a `PUT /products/{id}` to update keywords/sources
- On first boot, run `db/seed.py` to insert the Wealthsimple Trade product if none exists
- Store all config in the database, NOT in environment variables or config files
  (so it survives deployments and can be edited via the UI)

## Acceptance Criteria
- [ ] Database initialises with products, product_keywords, product_sources tables
- [ ] Seed script inserts Wealthsimple Trade product on first run
- [ ] `GET /products` returns list of active products
- [ ] `POST /products` creates a new product with keywords and sources
- [ ] Adding Xbox product with its keywords works end-to-end
