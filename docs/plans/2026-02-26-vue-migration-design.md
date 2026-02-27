# Vue Migration Design: Streamlit → FastAPI + Vue 3 SPA

**Date:** 2026-02-26
**Status:** Approved
**Branch:** ui-work

---

## Overview

Migrate the Wealthsimple Community Intelligence Platform dashboard from Streamlit (`ui/app.py`) to a modern web app using **FastAPI** (backend) + **Vue 3 + PrimeVue** (frontend), with a **Wealthsimple-inspired** visual design.

The Python ML pipeline (`pipeline/`) is **untouched**. The new web app replaces only the `ui/` layer.

---

## Architecture

**Approach:** Monorepo — FastAPI backend + Vue 3 SPA frontend, deployed together in production.

**Dev workflow:**
- `uvicorn api.main:app --reload` — FastAPI on port 8000
- `npm run dev` — Vite dev server on port 5173, proxies `/api/*` to FastAPI

**Production:**
- `npm run build` → `frontend/dist/`
- FastAPI serves `frontend/dist/` as static files at `/`
- Single process, single deployment unit

### Directory Structure

```
group_rider/
├── pipeline/              (unchanged — ML pipeline)
├── ui/                    (retired — keep for reference)
├── data/                  (unchanged — JSON files, later DB)
│
├── api/                   (NEW — FastAPI backend)
│   ├── main.py            (app factory, CORS, static file mount)
│   ├── routers/
│   │   ├── insights.py    (GET /api/insights, GET /api/insights/{id})
│   │   ├── reviews.py     (GET /api/reviews, PATCH /api/reviews/{id})
│   │   └── stats.py       (GET /api/stats)
│   ├── models.py          (Pydantic request/response models)
│   └── db.py              (SQLAlchemy session + engine — phase 2)
│
└── frontend/              (NEW — Vue 3 + PrimeVue + Vite)
    ├── src/
    │   ├── main.ts
    │   ├── App.vue
    │   ├── theme/
    │   │   └── wealthsimple.ts    (PrimeVue custom preset)
    │   ├── stores/
    │   │   ├── insights.ts        (Pinia — data + filters)
    │   │   └── reviews.ts         (Pinia — review actions)
    │   ├── components/
    │   │   ├── KpiTiles.vue
    │   │   ├── TopicsChart.vue
    │   │   ├── InsightCard.vue
    │   │   └── FilterSidebar.vue
    │   └── views/
    │       └── Dashboard.vue
    ├── index.html
    ├── vite.config.ts
    └── package.json
```

---

## API Contract

The API contract is the shared interface between frontend and database agent teams. Both teams build against these shapes.

### Endpoints

```
GET  /api/stats                   → Stats
GET  /api/insights                → Insight[]  (query: category, status, confidence, flagged)
GET  /api/insights/{id}           → Insight
GET  /api/reviews                 → Review[]
PATCH /api/reviews/{id}           → Review  (body: { status, note })
```

### Response Shapes

```typescript
interface Insight {
  id: string
  headline: string
  category: 'roadmap' | 'friction' | 'win' | 'other'
  confidence: 'high' | 'medium' | 'low'
  summary: string
  evidence: string[]
  product_action: string
  volume_signal: string
  needs_human_review: boolean
  review_reason: string | null
  canadian_context: string | null
  post_count: number
}

interface Review {
  insight_id: string
  status: 'pending' | 'escalate_to_product' | 'under_investigation' | 'known_issue' | 'out_of_scope' | 'dismissed'
  note: string
  updated_at: string  // ISO 8601 timestamp
}

interface Stats {
  total_posts: number
  total_insights: number
  pending_review: number
  flagged_for_review: number
}
```

---

## Frontend: Components & Theming

### Wealthsimple-Inspired Theme (PrimeVue custom preset)

| Design Token | Value | Usage |
|---|---|---|
| Primary | `#00C4A0` (WS mint green) | Buttons, active states, highlights |
| Surface | `#FFFFFF` / `#F7F8FA` | Cards, page background |
| Text primary | `#1A1A1A` | Headlines, body |
| Text muted | `#6B7280` | Labels, metadata, timestamps |
| Danger | `#EF4444` | Friction category |
| Info | `#2563EB` | Roadmap category |
| Success | `#059669` | Win category |
| Neutral | `#6B7280` | Other category |
| Font | Inter (Google Fonts) | All text |
| Border radius | `12px` (cards), `8px` (inputs) | Clean rounded look |

### Component Mapping (Streamlit → PrimeVue)

| Streamlit element | PrimeVue component |
|---|---|
| KPI metric tiles | `<Card>` with stat layout |
| Plotly bar chart | `<Chart>` (Chart.js wrapper) |
| Insight cards feed | `<DataView>` with card template |
| Sidebar filters | `<Drawer>` + `<Checkbox>` groups |
| Status dropdown | `<Select>` |
| Note input | `<Textarea>` |
| Save button | `<Button>` primary variant |
| Review flag badge | `<Tag severity="warn">` |
| Notifications | `<Toast>` on save success/error |
| Category badge | `<Tag>` with category color |
| Confidence indicator | `<Tag>` with severity |

---

## Database Design

**Strategy:** SQLite for local dev, PostgreSQL for production. SQLAlchemy ORM handles both with no code changes — switch via `DATABASE_URL` environment variable.

**Phase 1:** API reads/writes existing `data/insights/` JSON files (zero DB setup required to ship frontend).

**Phase 2:** Introduce SQLAlchemy models, migrate JSON → DB, update API routers to use DB sessions.

### Schema

```sql
-- Normalized raw source data
raw_posts (
  id            TEXT PRIMARY KEY,
  text          TEXT NOT NULL,
  timestamp     DATETIME NOT NULL,
  source        TEXT NOT NULL,   -- 'reddit' | 'google_play' | 'appstore'
  sentiment_score REAL,
  language      TEXT,
  topic_id      TEXT,
  metadata      JSON            -- source-specific: upvotes, rating, subreddit, app_version, etc.
)

-- AI-generated insight cards (one per topic cluster)
insights (
  id                TEXT PRIMARY KEY,
  headline          TEXT NOT NULL,
  category          TEXT NOT NULL,   -- 'roadmap' | 'friction' | 'win' | 'other'
  confidence        TEXT NOT NULL,   -- 'high' | 'medium' | 'low'
  summary           TEXT NOT NULL,
  evidence          JSON NOT NULL,   -- string[]
  product_action    TEXT NOT NULL,
  volume_signal     TEXT NOT NULL,
  needs_human_review BOOLEAN DEFAULT FALSE,
  review_reason     TEXT,
  canadian_context  TEXT,
  post_count        INTEGER DEFAULT 0,
  created_at        DATETIME DEFAULT CURRENT_TIMESTAMP
)

-- Human review actions
reviews (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  insight_id   TEXT NOT NULL REFERENCES insights(id),
  status       TEXT NOT NULL DEFAULT 'pending',
  note         TEXT DEFAULT '',
  updated_at   DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

**Rationale for single `raw_posts` table:** The ML pipeline already normalizes all sources to a common schema before writing NDJSON. Cross-source analytics (e.g., "all posts mentioning TFSA") are natural. Source-specific fields are preserved in the `metadata` JSON column. Can be split into per-source tables later if needed.

---

## Parallel Agent Team Strategy

Two independent agent teams can work in parallel **after the API contract is locked**.

### Phase 1 — Lock the contract (done: this design doc)

Both teams build against the Pydantic models in `api/models.py`.

### Phase 2 — Parallel execution

**Frontend Agent Team**
- Scaffold Vue 3 + PrimeVue + Vite in `frontend/`
- Implement all components against API contract using mock data
- Apply Wealthsimple theme preset
- No dependency on database team

**Database Agent Team**
- Add SQLAlchemy models matching the DB schema above
- Add `api/db.py` with session factory
- Update FastAPI routers to read from DB (initially: seed from existing JSON files)
- Implement migration script: `data/insights/insights.json` → DB

### Phase 3 — Integration

- Frontend points at real API (remove mocks)
- End-to-end smoke test
- Retire `ui/app.py`

---

## What Stays the Same

- `pipeline/` — all ML code untouched
- `data/` directory structure — JSON files remain as pipeline output; Phase 2 adds DB ingestion
- `pyproject.toml` — add `fastapi`, `uvicorn`, `sqlalchemy` to dependencies
- Environment variables — `.env` gains `DATABASE_URL` in Phase 2
