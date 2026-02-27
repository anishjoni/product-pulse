# Vue Migration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the Streamlit dashboard with a FastAPI backend + Vue 3 + PrimeVue frontend with Wealthsimple-inspired theming.

**Architecture:** FastAPI backend reads existing `data/insights/` JSON files and exposes a REST API. Vue 3 SPA calls that API. In production, FastAPI serves the built Vue bundle as static files. The ML pipeline (`pipeline/`) is untouched.

**Tech Stack:** Python 3.11, FastAPI, uvicorn, httpx (tests) | Vue 3, TypeScript, PrimeVue 4, Pinia, Vite, Chart.js | uv (Python), npm (frontend)

**Design doc:** `docs/plans/2026-02-26-vue-migration-design.md`

---

## Existing data format (read this before starting)

**`data/insights/insights.json`** — array of objects with:
- `topic_id` (int) — the unique identifier
- `headline`, `category`, `confidence`, `summary`, `evidence` (pipe-separated string), `product_action`, `volume_signal`
- `needs_human_review` (bool), `review_reason` (str|null), `canadian_context` (str|null)
- `n_posts` (int) — NOTE: this is `post_count` in the API
- `status` (str, embedded in insight — ignore this, use review_log instead)
- `top_words` (str) — used only by the chart

**`data/insights/review_log.json`** — dict keyed by `str(topic_id)`:
```json
{
  "1": {"action": "pending", "note": "", "reviewed_at": "2024-01-01T00:00:00"},
  "2": {"action": "escalate to product", "note": "JIRA-123", "reviewed_at": "2024-01-01T00:01:00"}
}
```
Note: `action` (not `status`), `reviewed_at` (not `updated_at`), status values use spaces ("escalate to product").

---

## Phase 1: FastAPI Backend (JSON-backed)

These tasks run sequentially first. They lock the API contract before parallel teams start.

---

### Task 1: Add FastAPI dependencies

**Files:**
- Modify: `pyproject.toml`

**Step 1: Add deps to pyproject.toml**

In the `dependencies` list, add after the `streamlit` line:

```toml
    # API backend
    "fastapi>=0.111.0",
    "uvicorn[standard]>=0.29.0",
```

In `[dependency-groups] dev`, add:
```toml
    "httpx>=0.27.0",
```

**Step 2: Sync**

```bash
uv sync
```

Expected: resolves without conflict.

**Step 3: Verify imports**

```bash
uv run python -c "import fastapi; import uvicorn; print('ok')"
```

Expected: `ok`

**Step 4: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "feat: add fastapi + uvicorn dependencies"
```

---

### Task 2: Pydantic models (API contract)

**Files:**
- Create: `api/__init__.py`
- Create: `api/models.py`
- Create: `tests/api/__init__.py`
- Create: `tests/api/test_models.py`

**Step 1: Create `api/__init__.py`** (empty)

**Step 2: Create `tests/api/__init__.py`** (empty)

**Step 3: Write the failing test**

```python
# tests/api/test_models.py
from api.models import Insight, Review, ReviewUpdate, Stats


def test_insight_model():
    data = {
        "id": "1",
        "headline": "TFSA over-contribution",
        "category": "friction",
        "confidence": "high",
        "summary": "Users are confused about TFSA limits.",
        "evidence": ["quote one", "quote two"],
        "product_action": "Add in-app limit calculator",
        "volume_signal": "47 posts over 6 months",
        "needs_human_review": True,
        "review_reason": "CRA penalty risk",
        "canadian_context": "TFSA limit is $7000 in 2024",
        "post_count": 47,
    }
    insight = Insight(**data)
    assert insight.id == "1"
    assert insight.category == "friction"
    assert len(insight.evidence) == 2


def test_review_model():
    review = Review(
        insight_id="1",
        status="pending",
        note="",
        updated_at="2024-01-01T00:00:00",
    )
    assert review.status == "pending"


def test_review_update_defaults():
    update = ReviewUpdate(status="known_issue")
    assert update.note == ""


def test_stats_model():
    stats = Stats(total_posts=1000, total_insights=48, pending_review=36, flagged_for_review=4)
    assert stats.pending_review == 36
```

**Step 4: Run test — expect failure**

```bash
uv run pytest tests/api/test_models.py -v
```

Expected: `ModuleNotFoundError: No module named 'api'`

**Step 5: Create `api/models.py`**

```python
# api/models.py
from typing import Literal

from pydantic import BaseModel

CategoryType = Literal["roadmap", "friction", "win", "other"]
ConfidenceType = Literal["high", "medium", "low"]
StatusType = Literal[
    "pending",
    "escalate_to_product",
    "under_investigation",
    "known_issue",
    "out_of_scope",
    "dismissed",
]


class Insight(BaseModel):
    id: str
    headline: str
    category: CategoryType
    confidence: ConfidenceType
    summary: str
    evidence: list[str]
    product_action: str
    volume_signal: str
    needs_human_review: bool
    review_reason: str | None
    canadian_context: str | None
    post_count: int


class Review(BaseModel):
    insight_id: str
    status: StatusType
    note: str
    updated_at: str


class ReviewUpdate(BaseModel):
    status: StatusType
    note: str = ""


class Stats(BaseModel):
    total_posts: int
    total_insights: int
    pending_review: int
    flagged_for_review: int
```

**Step 6: Run tests — expect pass**

```bash
uv run pytest tests/api/test_models.py -v
```

Expected: 4 passed.

**Step 7: Commit**

```bash
git add api/ tests/api/
git commit -m "feat: add API Pydantic models (Insight, Review, Stats)"
```

---

### Task 3: Data loader (JSON → models)

**Files:**
- Create: `api/data.py`
- Create: `tests/api/test_data.py`

The data loader maps the on-disk JSON format to API models. This is the only place that knows about `topic_id`, `n_posts`, `action`, `reviewed_at`.

**Step 1: Write failing test**

```python
# tests/api/test_data.py
import json
import tempfile
from pathlib import Path

import pytest

from api.data import load_insights, load_review_log, save_review


SAMPLE_INSIGHTS = [
    {
        "topic_id": 1,
        "headline": "TFSA over-contribution",
        "category": "friction",
        "confidence": "high",
        "summary": "Users confused about TFSA limits.",
        "evidence": '"quote one" | "quote two"',
        "product_action": "Add calculator",
        "volume_signal": "47 posts",
        "needs_human_review": True,
        "review_reason": "CRA risk",
        "canadian_context": "TFSA 2024 = $7000",
        "n_posts": 47,
        "top_words": "tfsa, limit, over",
        "status": "pending",
    }
]

SAMPLE_REVIEW_LOG = {
    "1": {"action": "known_issue", "note": "JIRA-42", "reviewed_at": "2024-01-01T00:00:00"}
}


@pytest.fixture
def tmp_data_dir(tmp_path):
    insights_dir = tmp_path / "insights"
    insights_dir.mkdir()
    (insights_dir / "insights.json").write_text(json.dumps(SAMPLE_INSIGHTS))
    (insights_dir / "review_log.json").write_text(json.dumps(SAMPLE_REVIEW_LOG))
    return insights_dir


def test_load_insights_maps_fields(tmp_data_dir):
    insights = load_insights(tmp_data_dir)
    assert len(insights) == 1
    i = insights[0]
    assert i.id == "1"
    assert i.post_count == 47
    assert i.evidence == ['"quote one"', '"quote two"']


def test_load_review_log(tmp_data_dir):
    reviews = load_review_log(tmp_data_dir)
    assert len(reviews) == 1
    r = reviews[0]
    assert r.insight_id == "1"
    assert r.status == "known_issue"
    assert r.note == "JIRA-42"
    assert r.updated_at == "2024-01-01T00:00:00"


def test_save_review(tmp_data_dir):
    from api.models import ReviewUpdate
    save_review("1", ReviewUpdate(status="dismissed", note="out of scope"), tmp_data_dir)
    reviews = load_review_log(tmp_data_dir)
    r = next(r for r in reviews if r.insight_id == "1")
    assert r.status == "dismissed"
    assert r.note == "out of scope"


def test_load_insights_falls_back_to_demo_when_missing(tmp_path):
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    insights = load_insights(empty_dir)
    assert len(insights) >= 1  # demo data
```

**Step 2: Run — expect failure**

```bash
uv run pytest tests/api/test_data.py -v
```

**Step 3: Create `api/data.py`**

```python
# api/data.py
"""Load/save insight data from the JSON files written by the pipeline."""

import json
from datetime import datetime
from pathlib import Path

from api.models import Insight, Review, ReviewUpdate

# Status values: API uses underscores, file uses spaces
_STATUS_TO_FILE = {
    "escalate_to_product": "escalate to product",
    "under_investigation": "under investigation",
    "known_issue": "known issue",
    "out_of_scope": "out of scope",
}
_STATUS_FROM_FILE = {v: k for k, v in _STATUS_TO_FILE.items()}

DEFAULT_DATA_DIR = Path("data/insights")


def _parse_evidence(raw: str | list) -> list[str]:
    """Split pipe-separated evidence string into list, or pass through if already list."""
    if isinstance(raw, list):
        return raw
    return [s.strip() for s in str(raw).split("|") if s.strip()]


def _normalize_status(action: str) -> str:
    return _STATUS_FROM_FILE.get(action, action)


def _denormalize_status(status: str) -> str:
    return _STATUS_TO_FILE.get(status, status)


def load_insights(data_dir: Path = DEFAULT_DATA_DIR) -> list[Insight]:
    path = data_dir / "insights.json"
    if not path.exists():
        return _demo_insights()
    raw = json.loads(path.read_text())
    if not raw:
        return _demo_insights()
    return [
        Insight(
            id=str(item["topic_id"]),
            headline=item["headline"],
            category=item["category"],
            confidence=item["confidence"],
            summary=item["summary"],
            evidence=_parse_evidence(item.get("evidence", "")),
            product_action=item["product_action"],
            volume_signal=item["volume_signal"],
            needs_human_review=item.get("needs_human_review", False),
            review_reason=item.get("review_reason"),
            canadian_context=item.get("canadian_context"),
            post_count=item.get("n_posts", 0),
        )
        for item in raw
    ]


def load_review_log(data_dir: Path = DEFAULT_DATA_DIR) -> list[Review]:
    path = data_dir / "review_log.json"
    if not path.exists():
        return []
    raw: dict = json.loads(path.read_text())
    return [
        Review(
            insight_id=insight_id,
            status=_normalize_status(entry.get("action", "pending")),
            note=entry.get("note", ""),
            updated_at=entry.get("reviewed_at", ""),
        )
        for insight_id, entry in raw.items()
    ]


def save_review(insight_id: str, update: ReviewUpdate, data_dir: Path = DEFAULT_DATA_DIR) -> Review:
    path = data_dir / "review_log.json"
    log: dict = json.loads(path.read_text()) if path.exists() else {}
    now = datetime.now().isoformat()
    log[insight_id] = {
        "action": _denormalize_status(update.status),
        "note": update.note,
        "reviewed_at": now,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(log, indent=2))
    return Review(insight_id=insight_id, status=update.status, note=update.note, updated_at=now)


def _demo_insights() -> list[Insight]:
    return [
        Insight(
            id="1",
            headline="TFSA over-contribution limits confusing users",
            category="friction",
            confidence="high",
            summary="Users are confused about annual TFSA contribution limits, leading to over-contributions and CRA penalties.",
            evidence=['"I got a penalty letter from CRA — had no idea I over-contributed."', '"WS should warn me when I\'m close to my TFSA limit."'],
            product_action="Add real-time TFSA contribution tracker with CRA limit warnings.",
            volume_signal="47 posts over 6 months",
            needs_human_review=True,
            review_reason="CRA penalty implications — validate with compliance before acting",
            canadian_context="2024 TFSA limit is $7,000; lifetime room varies by year of eligibility",
            post_count=47,
        ),
        Insight(
            id="2",
            headline="Instant deposit limits too low for active traders",
            category="friction",
            confidence="high",
            summary="Users want higher instant deposit limits. Current $1,500 limit frustrates active traders missing same-day opportunities.",
            evidence=['"$1,500 instant limit is a joke when you\'re trying to catch a dip."', '"Questrade gives me $3,000 instant — why is WS so low?"'],
            product_action="Review instant deposit risk model. Consider tiered limits based on account history.",
            volume_signal="62 posts, consistent complaints",
            needs_human_review=False,
            review_reason=None,
            canadian_context="Instant deposit is a key differentiator vs Questrade for active traders",
            post_count=62,
        ),
    ]
```

**Step 4: Run tests — expect pass**

```bash
uv run pytest tests/api/test_data.py -v
```

Expected: 4 passed.

**Step 5: Commit**

```bash
git add api/data.py tests/api/test_data.py
git commit -m "feat: add data loader — maps JSON files to API models"
```

---

### Task 4: Stats, Insights, Reviews routers + FastAPI app

**Files:**
- Create: `api/routers/__init__.py`
- Create: `api/routers/stats.py`
- Create: `api/routers/insights.py`
- Create: `api/routers/reviews.py`
- Create: `api/main.py`
- Create: `tests/api/test_routes.py`

**Step 1: Write failing tests**

```python
# tests/api/test_routes.py
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    """TestClient with a temporary data directory containing demo-seeded files."""
    insights_dir = tmp_path / "insights"
    insights_dir.mkdir()

    # Write demo insights
    demo = [
        {
            "topic_id": 1, "headline": "TFSA confusion", "category": "friction",
            "confidence": "high", "summary": "Users confused.",
            "evidence": '"quote one" | "quote two"',
            "product_action": "Add calculator", "volume_signal": "47 posts",
            "needs_human_review": True, "review_reason": "CRA risk",
            "canadian_context": None, "n_posts": 47, "top_words": "tfsa", "status": "pending",
        },
        {
            "topic_id": 2, "headline": "Round-ups loved", "category": "win",
            "confidence": "high", "summary": "Users love round-ups.",
            "evidence": '"great feature"',
            "product_action": "Extend to RRSP", "volume_signal": "89 posts",
            "needs_human_review": False, "review_reason": None,
            "canadian_context": None, "n_posts": 89, "top_words": "round", "status": "pending",
        },
    ]
    (insights_dir / "insights.json").write_text(json.dumps(demo))

    # Patch DEFAULT_DATA_DIR before importing app
    import api.data as data_module
    monkeypatch.setattr(data_module, "DEFAULT_DATA_DIR", insights_dir)

    from api.main import app
    return TestClient(app)


def test_get_stats(client):
    r = client.get("/api/stats")
    assert r.status_code == 200
    data = r.json()
    assert data["total_insights"] == 2
    assert data["total_posts"] == 136  # 47 + 89
    assert data["pending_review"] == 2
    assert data["flagged_for_review"] == 1


def test_get_insights(client):
    r = client.get("/api/insights")
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 2
    assert items[0]["id"] == "1"
    assert items[0]["post_count"] == 47


def test_get_insights_filter_by_category(client):
    r = client.get("/api/insights?category=win")
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 1
    assert items[0]["category"] == "win"


def test_get_insight_by_id(client):
    r = client.get("/api/insights/1")
    assert r.status_code == 200
    assert r.json()["headline"] == "TFSA confusion"


def test_get_insight_not_found(client):
    r = client.get("/api/insights/999")
    assert r.status_code == 404


def test_patch_review(client):
    r = client.patch("/api/reviews/1", json={"status": "known_issue", "note": "JIRA-42"})
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "known_issue"
    assert data["note"] == "JIRA-42"
    assert data["insight_id"] == "1"


def test_get_reviews(client):
    # Patch one first
    client.patch("/api/reviews/1", json={"status": "dismissed", "note": ""})
    r = client.get("/api/reviews")
    assert r.status_code == 200
    reviews = r.json()
    assert any(rv["insight_id"] == "1" for rv in reviews)
```

**Step 2: Run — expect failure**

```bash
uv run pytest tests/api/test_routes.py -v
```

**Step 3: Create `api/routers/__init__.py`** (empty)

**Step 4: Create `api/routers/stats.py`**

```python
# api/routers/stats.py
from fastapi import APIRouter
from api.data import load_insights, load_review_log
from api.models import Stats

router = APIRouter()


@router.get("/api/stats", response_model=Stats)
def get_stats() -> Stats:
    insights = load_insights()
    reviews = load_review_log()
    reviewed_ids = {r.insight_id for r in reviews if r.status != "pending"}
    return Stats(
        total_posts=sum(i.post_count for i in insights),
        total_insights=len(insights),
        pending_review=sum(1 for i in insights if i.id not in reviewed_ids),
        flagged_for_review=sum(1 for i in insights if i.needs_human_review),
    )
```

**Step 5: Create `api/routers/insights.py`**

```python
# api/routers/insights.py
from fastapi import APIRouter, HTTPException, Query
from api.data import load_insights
from api.models import Insight

router = APIRouter()


@router.get("/api/insights", response_model=list[Insight])
def list_insights(
    category: str | None = Query(None),
    confidence: str | None = Query(None),
    flagged: bool | None = Query(None),
) -> list[Insight]:
    items = load_insights()
    if category:
        items = [i for i in items if i.category == category]
    if confidence:
        items = [i for i in items if i.confidence == confidence]
    if flagged is not None:
        items = [i for i in items if i.needs_human_review == flagged]
    return items


@router.get("/api/insights/{insight_id}", response_model=Insight)
def get_insight(insight_id: str) -> Insight:
    insights = load_insights()
    match = next((i for i in insights if i.id == insight_id), None)
    if not match:
        raise HTTPException(status_code=404, detail="Insight not found")
    return match
```

**Step 6: Create `api/routers/reviews.py`**

```python
# api/routers/reviews.py
from fastapi import APIRouter
from api.data import load_review_log, save_review
from api.models import Review, ReviewUpdate

router = APIRouter()


@router.get("/api/reviews", response_model=list[Review])
def list_reviews() -> list[Review]:
    return load_review_log()


@router.patch("/api/reviews/{insight_id}", response_model=Review)
def update_review(insight_id: str, update: ReviewUpdate) -> Review:
    return save_review(insight_id, update)
```

**Step 7: Create `api/main.py`**

```python
# api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import insights, reviews, stats

app = FastAPI(title="WS Community Intelligence API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_methods=["GET", "PATCH"],
    allow_headers=["*"],
)

app.include_router(stats.router)
app.include_router(insights.router)
app.include_router(reviews.router)
```

**Step 8: Run tests — expect pass**

```bash
uv run pytest tests/api/ -v
```

Expected: all pass.

**Step 9: Manual smoke test**

```bash
uv run uvicorn api.main:app --reload
# In another terminal:
curl http://localhost:8000/api/stats
```

Expected: JSON with `total_insights`, `total_posts`, etc.

**Step 10: Commit**

```bash
git add api/ tests/api/
git commit -m "feat: FastAPI backend with stats, insights, reviews endpoints"
```

---

## Phase 2A: Vue 3 Frontend (Frontend Agent)

> This phase runs **in parallel** with Phase 2B. The frontend builds against the API contract defined in Phase 1. Use mock data matching the Insight/Review/Stats shapes while the API runs locally.

---

### Task 5: Scaffold Vue 3 project

**Files:**
- Create: `frontend/` (entire directory via Vite)

**Step 1: Scaffold**

```bash
cd /path/to/group_rider
npm create vite@latest frontend -- --template vue-ts
cd frontend
npm install
```

**Step 2: Install PrimeVue and dependencies**

```bash
npm install primevue @primevue/themes primeicons chart.js pinia axios
npm install -D @types/node
```

**Step 3: Update `frontend/vite.config.ts`**

```typescript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: { '@': resolve(__dirname, './src') },
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

**Step 4: Verify scaffold runs**

```bash
npm run dev
```

Expected: Vite dev server at http://localhost:5173 with default Vue app.

**Step 5: Commit**

```bash
cd ..  # back to group_rider root
git add frontend/
git commit -m "feat: scaffold Vue 3 + PrimeVue + Vite frontend"
```

---

### Task 6: PrimeVue setup + Wealthsimple theme

**Files:**
- Create: `frontend/src/theme/wealthsimple.ts`
- Modify: `frontend/src/main.ts`

**Step 1: Create `frontend/src/theme/wealthsimple.ts`**

```typescript
// frontend/src/theme/wealthsimple.ts
import { definePreset } from '@primevue/themes'
import Aura from '@primevue/themes/aura'

export const WealthsimpleTheme = definePreset(Aura, {
  semantic: {
    primary: {
      50:  '{teal.50}',
      100: '{teal.100}',
      200: '{teal.200}',
      300: '{teal.300}',
      400: '{teal.400}',
      500: '#00C4A0',
      600: '#00A888',
      700: '#008C72',
      800: '#006F5A',
      900: '#005444',
      950: '#003830',
    },
    colorScheme: {
      light: {
        surface: {
          0:   '#ffffff',
          50:  '#F7F8FA',
          100: '#F0F1F3',
          200: '#E5E7EB',
          300: '#D1D5DB',
          400: '#9CA3AF',
          500: '#6B7280',
          600: '#4B5563',
          700: '#374151',
          800: '#1F2937',
          900: '#111827',
          950: '#030712',
        },
      },
    },
  },
})
```

**Step 2: Update `frontend/src/main.ts`**

```typescript
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import PrimeVue from 'primevue/config'
import ToastService from 'primevue/toastservice'
import 'primeicons/primeicons.css'

import App from './App.vue'
import { WealthsimpleTheme } from './theme/wealthsimple'

const app = createApp(App)

app.use(createPinia())
app.use(PrimeVue, {
  theme: {
    preset: WealthsimpleTheme,
    options: {
      darkModeSelector: '.dark-mode',
    },
  },
})
app.use(ToastService)

app.mount('#app')
```

**Step 3: Add Inter font to `frontend/index.html`**

Add inside `<head>`:
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>* { font-family: 'Inter', sans-serif; }</style>
```

**Step 4: Verify — run dev server, no console errors**

```bash
cd frontend && npm run dev
```

**Step 5: Commit**

```bash
git add frontend/src/theme/ frontend/src/main.ts frontend/index.html
git commit -m "feat: add Wealthsimple PrimeVue theme preset"
```

---

### Task 7: TypeScript types + API client

**Files:**
- Create: `frontend/src/types/index.ts`
- Create: `frontend/src/api/client.ts`

**Step 1: Create `frontend/src/types/index.ts`**

```typescript
export type Category = 'roadmap' | 'friction' | 'win' | 'other'
export type Confidence = 'high' | 'medium' | 'low'
export type ReviewStatus =
  | 'pending'
  | 'escalate_to_product'
  | 'under_investigation'
  | 'known_issue'
  | 'out_of_scope'
  | 'dismissed'

export interface Insight {
  id: string
  headline: string
  category: Category
  confidence: Confidence
  summary: string
  evidence: string[]
  product_action: string
  volume_signal: string
  needs_human_review: boolean
  review_reason: string | null
  canadian_context: string | null
  post_count: number
}

export interface Review {
  insight_id: string
  status: ReviewStatus
  note: string
  updated_at: string
}

export interface ReviewUpdate {
  status: ReviewStatus
  note: string
}

export interface Stats {
  total_posts: number
  total_insights: number
  pending_review: number
  flagged_for_review: number
}
```

**Step 2: Create `frontend/src/api/client.ts`**

```typescript
import axios from 'axios'
import type { Insight, Review, ReviewUpdate, Stats } from '@/types'

const http = axios.create({ baseURL: '/api' })

export const api = {
  getStats: (): Promise<Stats> =>
    http.get('/stats').then(r => r.data),

  getInsights: (params?: { category?: string; confidence?: string; flagged?: boolean }): Promise<Insight[]> =>
    http.get('/insights', { params }).then(r => r.data),

  getInsight: (id: string): Promise<Insight> =>
    http.get(`/insights/${id}`).then(r => r.data),

  getReviews: (): Promise<Review[]> =>
    http.get('/reviews').then(r => r.data),

  updateReview: (insightId: string, update: ReviewUpdate): Promise<Review> =>
    http.patch(`/reviews/${insightId}`, update).then(r => r.data),
}
```

**Step 3: Commit**

```bash
git add frontend/src/types/ frontend/src/api/
git commit -m "feat: add TypeScript types and API client"
```

---

### Task 8: Pinia stores

**Files:**
- Create: `frontend/src/stores/insights.ts`
- Create: `frontend/src/stores/reviews.ts`

**Step 1: Create `frontend/src/stores/insights.ts`**

```typescript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/api/client'
import type { Insight, Stats, Category, Confidence } from '@/types'

export const useInsightsStore = defineStore('insights', () => {
  const insights = ref<Insight[]>([])
  const stats = ref<Stats | null>(null)
  const loading = ref(false)

  const filters = ref({
    categories: ['roadmap', 'friction', 'win', 'other'] as Category[],
    confidences: ['high', 'medium', 'low'] as Confidence[],
    flaggedOnly: false,
  })

  const filtered = computed(() =>
    insights.value.filter(i => {
      if (!filters.value.categories.includes(i.category)) return false
      if (!filters.value.confidences.includes(i.confidence)) return false
      if (filters.value.flaggedOnly && !i.needs_human_review) return false
      return true
    })
  )

  const topByVolume = computed(() =>
    [...insights.value].sort((a, b) => b.post_count - a.post_count).slice(0, 8)
  )

  async function fetchAll() {
    loading.value = true
    try {
      const [insightData, statsData] = await Promise.all([api.getInsights(), api.getStats()])
      insights.value = insightData
      stats.value = statsData
    } finally {
      loading.value = false
    }
  }

  return { insights, stats, loading, filters, filtered, topByVolume, fetchAll }
})
```

**Step 2: Create `frontend/src/stores/reviews.ts`**

```typescript
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '@/api/client'
import type { Review, ReviewUpdate } from '@/types'

export const useReviewsStore = defineStore('reviews', () => {
  const reviews = ref<Review[]>([])
  const saving = ref(false)

  function getReview(insightId: string): Review | undefined {
    return reviews.value.find(r => r.insight_id === insightId)
  }

  async function fetchReviews() {
    reviews.value = await api.getReviews()
  }

  async function saveReview(insightId: string, update: ReviewUpdate) {
    saving.value = true
    try {
      const saved = await api.updateReview(insightId, update)
      const idx = reviews.value.findIndex(r => r.insight_id === insightId)
      if (idx >= 0) reviews.value[idx] = saved
      else reviews.value.push(saved)
    } finally {
      saving.value = false
    }
  }

  return { reviews, saving, getReview, fetchReviews, saveReview }
})
```

**Step 3: Commit**

```bash
git add frontend/src/stores/
git commit -m "feat: add Pinia stores for insights and reviews"
```

---

### Task 9: KpiTiles component

**Files:**
- Create: `frontend/src/components/KpiTiles.vue`

```vue
<!-- frontend/src/components/KpiTiles.vue -->
<template>
  <div class="kpi-row">
    <div v-for="tile in tiles" :key="tile.label" class="kpi-card">
      <span class="kpi-value">{{ tile.value }}</span>
      <span class="kpi-label">{{ tile.label }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Stats } from '@/types'

const props = defineProps<{ stats: Stats }>()

const tiles = computed(() => [
  { label: 'Posts analyzed',  value: props.stats.total_posts.toLocaleString() },
  { label: 'Insight cards',   value: props.stats.total_insights },
  { label: 'Pending review',  value: props.stats.pending_review },
  { label: 'Flagged',         value: props.stats.flagged_for_review },
])
</script>

<style scoped>
.kpi-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
  margin-bottom: 1.5rem;
}
.kpi-card {
  background: var(--p-surface-0);
  border: 1px solid var(--p-surface-200);
  border-radius: 12px;
  padding: 1.25rem 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}
.kpi-value {
  font-size: 2rem;
  font-weight: 700;
  color: var(--p-surface-900);
  line-height: 1;
}
.kpi-label {
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--p-surface-500);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
</style>
```

**Commit:**
```bash
git add frontend/src/components/KpiTiles.vue
git commit -m "feat: add KpiTiles component"
```

---

### Task 10: TopicsChart component

**Files:**
- Create: `frontend/src/components/TopicsChart.vue`

```vue
<!-- frontend/src/components/TopicsChart.vue -->
<template>
  <div class="chart-card">
    <h3 class="chart-title">Top topics by post volume</h3>
    <Chart type="bar" :data="chartData" :options="chartOptions" style="height: 280px" />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import Chart from 'primevue/chart'
import type { Insight } from '@/types'

const CATEGORY_COLORS: Record<string, string> = {
  roadmap:  '#2563EB',
  friction: '#EF4444',
  win:      '#059669',
  other:    '#6B7280',
}

const props = defineProps<{ insights: Insight[] }>()

const chartData = computed(() => ({
  labels: props.insights.map(i => i.headline.length > 42 ? i.headline.slice(0, 42) + '…' : i.headline),
  datasets: [{
    data: props.insights.map(i => i.post_count),
    backgroundColor: props.insights.map(i => CATEGORY_COLORS[i.category] ?? '#6B7280'),
    borderRadius: 6,
  }],
}))

const chartOptions = {
  indexAxis: 'y' as const,
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { display: false } },
  scales: {
    x: { grid: { color: '#E5E7EB' }, ticks: { color: '#6B7280' } },
    y: { grid: { display: false }, ticks: { color: '#1A1A1A', font: { size: 12 } } },
  },
}
</script>

<style scoped>
.chart-card {
  background: var(--p-surface-0);
  border: 1px solid var(--p-surface-200);
  border-radius: 12px;
  padding: 1.25rem 1.5rem;
  margin-bottom: 1.5rem;
}
.chart-title {
  font-size: 0.9375rem;
  font-weight: 600;
  color: var(--p-surface-900);
  margin: 0 0 1rem;
}
</style>
```

**Commit:**
```bash
git add frontend/src/components/TopicsChart.vue
git commit -m "feat: add TopicsChart component"
```

---

### Task 11: FilterSidebar component

**Files:**
- Create: `frontend/src/components/FilterSidebar.vue`

```vue
<!-- frontend/src/components/FilterSidebar.vue -->
<template>
  <div class="filter-sidebar">
    <h3 class="filter-title">Filters</h3>

    <div class="filter-group">
      <p class="filter-group-label">Category</p>
      <div v-for="cat in CATEGORIES" :key="cat.value" class="filter-item">
        <Checkbox v-model="filters.categories" :inputId="cat.value" :value="cat.value" />
        <label :for="cat.value">{{ cat.label }}</label>
      </div>
    </div>

    <div class="filter-group">
      <p class="filter-group-label">Confidence</p>
      <div v-for="conf in CONFIDENCES" :key="conf.value" class="filter-item">
        <Checkbox v-model="filters.confidences" :inputId="conf.value" :value="conf.value" />
        <label :for="conf.value">{{ conf.label }}</label>
      </div>
    </div>

    <div class="filter-group">
      <div class="filter-item">
        <Checkbox v-model="filters.flaggedOnly" inputId="flagged" binary />
        <label for="flagged">Flagged for review only</label>
      </div>
    </div>

    <div class="review-progress">
      <p class="filter-group-label">Review progress</p>
      <ProgressBar :value="progressPct" />
      <p class="progress-text">{{ reviewedCount }}/{{ totalCount }} ({{ progressPct }}%)</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import Checkbox from 'primevue/checkbox'
import ProgressBar from 'primevue/progressbar'
import { useInsightsStore } from '@/stores/insights'
import { useReviewsStore } from '@/stores/reviews'

const insightsStore = useInsightsStore()
const reviewsStore = useReviewsStore()
const filters = insightsStore.filters

const CATEGORIES = [
  { value: 'roadmap',  label: '🗺️ Roadmap' },
  { value: 'friction', label: '🔥 Friction' },
  { value: 'win',      label: '🏆 Win' },
  { value: 'other',    label: '📌 Other' },
]
const CONFIDENCES = [
  { value: 'high',   label: '🟢 High' },
  { value: 'medium', label: '🟡 Medium' },
  { value: 'low',    label: '🔴 Low' },
]

const totalCount = computed(() => insightsStore.insights.length)
const reviewedCount = computed(() =>
  reviewsStore.reviews.filter(r => r.status !== 'pending').length
)
const progressPct = computed(() =>
  totalCount.value ? Math.round((reviewedCount.value / totalCount.value) * 100) : 0
)
</script>

<style scoped>
.filter-sidebar {
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}
.filter-title {
  font-size: 1rem;
  font-weight: 700;
  color: var(--p-surface-900);
  margin: 0;
}
.filter-group { display: flex; flex-direction: column; gap: 0.5rem; }
.filter-group-label {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--p-surface-500);
  margin: 0;
}
.filter-item { display: flex; align-items: center; gap: 0.5rem; font-size: 0.875rem; }
.progress-text { font-size: 0.8125rem; color: var(--p-surface-500); margin: 0.25rem 0 0; }
</style>
```

**Commit:**
```bash
git add frontend/src/components/FilterSidebar.vue
git commit -m "feat: add FilterSidebar component"
```

---

### Task 12: InsightCard component

**Files:**
- Create: `frontend/src/components/InsightCard.vue`

```vue
<!-- frontend/src/components/InsightCard.vue -->
<template>
  <div class="insight-card" :class="insight.category">
    <div class="card-header">
      <div class="card-meta">
        <span class="category-badge" :style="{ color: CATEGORY_COLORS[insight.category] }">
          {{ CATEGORY_ICONS[insight.category] }} {{ CATEGORY_LABELS[insight.category] }}
        </span>
        <Tag :severity="confidenceSeverity" :value="insight.confidence.toUpperCase()" rounded />
        <span class="post-count">{{ insight.post_count }} posts</span>
      </div>
      <Tag v-if="insight.needs_human_review" severity="warn" value="⚠ Needs Review" rounded />
    </div>

    <h3 class="headline">{{ insight.headline }}</h3>
    <p class="summary">{{ insight.summary }}</p>

    <div class="evidence-block">
      <p class="section-label">Evidence</p>
      <blockquote v-for="(q, i) in insight.evidence" :key="i" class="quote">{{ q }}</blockquote>
    </div>

    <div class="action-block">
      <p class="section-label">Product action</p>
      <p class="action-text">{{ insight.product_action }}</p>
    </div>

    <p v-if="insight.canadian_context" class="canadian-context">
      🍁 {{ insight.canadian_context }}
    </p>

    <div class="review-controls">
      <Select
        v-model="localStatus"
        :options="STATUS_OPTIONS"
        optionLabel="label"
        optionValue="value"
        placeholder="Set status"
        class="status-select"
      />
      <Textarea v-model="localNote" placeholder="Add note or ticket link…" rows="2" autoResize />
      <Button
        label="Save"
        :loading="saving"
        @click="handleSave"
        size="small"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import Tag from 'primevue/tag'
import Select from 'primevue/select'
import Textarea from 'primevue/textarea'
import Button from 'primevue/button'
import { useToast } from 'primevue/usetoast'
import { useReviewsStore } from '@/stores/reviews'
import type { Insight } from '@/types'

const props = defineProps<{ insight: Insight }>()

const reviewsStore = useReviewsStore()
const toast = useToast()
const saving = ref(false)

const existingReview = computed(() => reviewsStore.getReview(props.insight.id))
const localStatus = ref(existingReview.value?.status ?? 'pending')
const localNote = ref(existingReview.value?.note ?? '')

watch(existingReview, r => {
  if (r) { localStatus.value = r.status; localNote.value = r.note }
})

async function handleSave() {
  saving.value = true
  try {
    await reviewsStore.saveReview(props.insight.id, { status: localStatus.value, note: localNote.value })
    toast.add({ severity: 'success', summary: 'Saved', life: 2000 })
  } catch {
    toast.add({ severity: 'error', summary: 'Save failed', life: 3000 })
  } finally {
    saving.value = false
  }
}

const CATEGORY_COLORS: Record<string, string> = {
  roadmap: '#2563EB', friction: '#EF4444', win: '#059669', other: '#6B7280',
}
const CATEGORY_ICONS: Record<string, string> = {
  roadmap: '🗺️', friction: '🔥', win: '🏆', other: '📌',
}
const CATEGORY_LABELS: Record<string, string> = {
  roadmap: 'Roadmap Opportunity', friction: 'Friction / Pain Point', win: 'Win', other: 'Other',
}

const STATUS_OPTIONS = [
  { label: 'Pending',              value: 'pending' },
  { label: 'Escalate to product',  value: 'escalate_to_product' },
  { label: 'Under investigation',  value: 'under_investigation' },
  { label: 'Known issue',          value: 'known_issue' },
  { label: 'Out of scope',         value: 'out_of_scope' },
  { label: 'Dismissed',            value: 'dismissed' },
]

const confidenceSeverity = computed(() => ({
  high: 'success', medium: 'warn', low: 'danger',
}[props.insight.confidence] ?? 'info'))
</script>

<style scoped>
.insight-card {
  background: var(--p-surface-0);
  border: 1px solid var(--p-surface-200);
  border-radius: 12px;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.875rem;
}
.card-header { display: flex; justify-content: space-between; align-items: flex-start; }
.card-meta { display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap; }
.category-badge { font-size: 0.8125rem; font-weight: 600; }
.post-count { font-size: 0.8125rem; color: var(--p-surface-500); }
.headline { font-size: 1.0625rem; font-weight: 700; color: var(--p-surface-900); margin: 0; }
.summary { font-size: 0.9rem; color: var(--p-surface-700); margin: 0; line-height: 1.6; }
.section-label { font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: var(--p-surface-500); margin: 0 0 0.25rem; }
.quote { border-left: 3px solid var(--p-surface-200); margin: 0.25rem 0; padding-left: 0.75rem; font-size: 0.875rem; color: var(--p-surface-600); font-style: italic; }
.action-text { font-size: 0.9rem; color: var(--p-surface-700); margin: 0; line-height: 1.6; }
.canadian-context { font-size: 0.8125rem; color: var(--p-surface-500); background: var(--p-surface-50); border-radius: 8px; padding: 0.5rem 0.75rem; margin: 0; }
.review-controls { display: flex; flex-direction: column; gap: 0.5rem; padding-top: 0.5rem; border-top: 1px solid var(--p-surface-100); }
.status-select { width: 100%; }
</style>
```

**Commit:**
```bash
git add frontend/src/components/InsightCard.vue
git commit -m "feat: add InsightCard component with review controls"
```

---

### Task 13: Dashboard view + App.vue

**Files:**
- Create: `frontend/src/views/Dashboard.vue`
- Modify: `frontend/src/App.vue`

**Step 1: Create `frontend/src/views/Dashboard.vue`**

```vue
<!-- frontend/src/views/Dashboard.vue -->
<template>
  <div class="dashboard">
    <aside class="sidebar">
      <div class="sidebar-brand">
        <span class="brand-name">WS Intelligence</span>
      </div>
      <FilterSidebar />
    </aside>

    <main class="main-content">
      <header class="page-header">
        <h1 class="page-title">Community Intelligence</h1>
        <p class="page-subtitle">AI finds the signal. You decide what to build.</p>
      </header>

      <KpiTiles v-if="insightsStore.stats" :stats="insightsStore.stats" />
      <TopicsChart :insights="insightsStore.topByVolume" />

      <div class="cards-header">
        <h2 class="cards-title">Insight Cards</h2>
        <span class="cards-count">{{ insightsStore.filtered.length }} insights</span>
      </div>

      <div v-if="insightsStore.loading" class="loading-state">
        <ProgressSpinner />
      </div>
      <div v-else-if="insightsStore.filtered.length === 0" class="empty-state">
        <p>No insights match your filters.</p>
      </div>
      <div v-else class="cards-grid">
        <InsightCard
          v-for="insight in insightsStore.filtered"
          :key="insight.id"
          :insight="insight"
        />
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import ProgressSpinner from 'primevue/progressspinner'
import KpiTiles from '@/components/KpiTiles.vue'
import TopicsChart from '@/components/TopicsChart.vue'
import FilterSidebar from '@/components/FilterSidebar.vue'
import InsightCard from '@/components/InsightCard.vue'
import { useInsightsStore } from '@/stores/insights'
import { useReviewsStore } from '@/stores/reviews'

const insightsStore = useInsightsStore()
const reviewsStore = useReviewsStore()

onMounted(async () => {
  await Promise.all([insightsStore.fetchAll(), reviewsStore.fetchReviews()])
})
</script>

<style scoped>
.dashboard { display: flex; min-height: 100vh; background: var(--p-surface-50); }
.sidebar {
  width: 240px;
  flex-shrink: 0;
  background: var(--p-surface-0);
  border-right: 1px solid var(--p-surface-200);
  display: flex;
  flex-direction: column;
}
.sidebar-brand {
  padding: 1.25rem 1rem;
  border-bottom: 1px solid var(--p-surface-200);
}
.brand-name { font-size: 1rem; font-weight: 700; color: var(--p-primary-500); }
.main-content { flex: 1; padding: 2rem; max-width: 1100px; }
.page-header { margin-bottom: 1.5rem; }
.page-title { font-size: 1.75rem; font-weight: 800; color: var(--p-surface-900); margin: 0; }
.page-subtitle { font-size: 0.9rem; color: var(--p-surface-500); margin: 0.25rem 0 0; }
.cards-header { display: flex; align-items: baseline; gap: 0.75rem; margin-bottom: 1rem; }
.cards-title { font-size: 1.125rem; font-weight: 700; margin: 0; }
.cards-count { font-size: 0.875rem; color: var(--p-surface-500); }
.cards-grid { display: flex; flex-direction: column; gap: 1rem; }
.loading-state, .empty-state { text-align: center; padding: 3rem; color: var(--p-surface-500); }
</style>
```

**Step 2: Replace `frontend/src/App.vue`**

```vue
<template>
  <Toast />
  <Dashboard />
</template>

<script setup lang="ts">
import Toast from 'primevue/toast'
import Dashboard from '@/views/Dashboard.vue'
</script>

<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: #F7F8FA; color: #1A1A1A; }
</style>
```

**Step 3: Delete unused files**

```bash
rm frontend/src/components/HelloWorld.vue frontend/src/assets/vue.svg
```

**Step 4: Run dev server and verify full UI**

```bash
cd frontend && npm run dev
# In another terminal: uv run uvicorn api.main:app --reload
```

Open http://localhost:5173 — should show full dashboard with data from API.

**Step 5: Commit**

```bash
git add frontend/src/views/ frontend/src/App.vue
git commit -m "feat: add Dashboard view — full layout with sidebar, chart, insight cards"
```

---

### Task 14: Production build integration

**Files:**
- Modify: `api/main.py`

**Step 1: Update `api/main.py` to serve Vue build**

```python
# api/main.py
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.routers import insights, reviews, stats

app = FastAPI(title="WS Community Intelligence API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET", "PATCH"],
    allow_headers=["*"],
)

app.include_router(stats.router)
app.include_router(insights.router)
app.include_router(reviews.router)

# Serve Vue SPA in production
_dist = Path(__file__).parent.parent / "frontend" / "dist"
if _dist.exists():
    app.mount("/", StaticFiles(directory=_dist, html=True), name="spa")
```

**Step 2: Add `aiofiles` for static file serving**

```bash
uv add aiofiles
```

**Step 3: Test production build**

```bash
cd frontend && npm run build
cd ..
uv run uvicorn api.main:app
```

Open http://localhost:8000 — should show the Vue app served by FastAPI.

**Step 4: Commit**

```bash
git add api/main.py pyproject.toml uv.lock frontend/dist/
git commit -m "feat: FastAPI serves Vue SPA in production"
```

---

## Phase 2B: Database Layer (Database Agent)

> This phase runs **in parallel** with Phase 2A. The database agent does NOT touch `frontend/` or the API routers until the schema is proven.

---

### Task 15: SQLAlchemy setup

**Files:**
- Modify: `pyproject.toml` (add `sqlalchemy`, `alembic`)
- Create: `api/db.py`

**Step 1: Add dependencies**

```toml
# In pyproject.toml dependencies:
"sqlalchemy>=2.0.0",
"alembic>=1.13.0",
```

```bash
uv sync
```

**Step 2: Create `api/db.py`**

```python
# api/db.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/app.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Step 3: Commit**

```bash
git add api/db.py pyproject.toml uv.lock
git commit -m "feat: add SQLAlchemy engine + session factory"
```

---

### Task 16: SQLAlchemy ORM models

**Files:**
- Create: `api/orm_models.py`
- Create: `tests/api/test_orm_models.py`

**Step 1: Write failing test**

```python
# tests/api/test_orm_models.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from api.db import Base
from api.orm_models import RawPost, InsightORM, ReviewORM


def make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_create_insight(session=None):
    session = session or make_session()
    insight = InsightORM(
        id="1",
        headline="TFSA confusion",
        category="friction",
        confidence="high",
        summary="Users confused.",
        evidence='["quote one", "quote two"]',
        product_action="Add calculator",
        volume_signal="47 posts",
        needs_human_review=True,
        post_count=47,
    )
    session.add(insight)
    session.commit()
    result = session.get(InsightORM, "1")
    assert result.headline == "TFSA confusion"
    assert result.post_count == 47


def test_create_review():
    session = make_session()
    # Need insight first for FK
    test_create_insight(session)
    review = ReviewORM(insight_id="1", status="known_issue", note="JIRA-42")
    session.add(review)
    session.commit()
    assert session.query(ReviewORM).count() == 1
```

**Step 2: Create `api/orm_models.py`**

```python
# api/orm_models.py
from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from api.db import Base


class RawPost(Base):
    __tablename__ = "raw_posts"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    source: Mapped[str] = mapped_column(Text, nullable=False)  # reddit | google_play | appstore
    sentiment_score: Mapped[float | None] = mapped_column()
    language: Mapped[str | None] = mapped_column(Text)
    topic_id: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[str | None] = mapped_column(Text)  # JSON blob for source-specific fields


class InsightORM(Base):
    __tablename__ = "insights"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    headline: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[str] = mapped_column(Text, nullable=False)  # JSON array
    product_action: Mapped[str] = mapped_column(Text, nullable=False)
    volume_signal: Mapped[str] = mapped_column(Text, nullable=False)
    needs_human_review: Mapped[bool] = mapped_column(Boolean, default=False)
    review_reason: Mapped[str | None] = mapped_column(Text)
    canadian_context: Mapped[str | None] = mapped_column(Text)
    post_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    review: Mapped["ReviewORM | None"] = relationship("ReviewORM", back_populates="insight", uselist=False)


class ReviewORM(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    insight_id: Mapped[str] = mapped_column(Text, ForeignKey("insights.id"), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="pending")
    note: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    insight: Mapped["InsightORM"] = relationship("InsightORM", back_populates="review")
```

**Step 3: Run tests — expect pass**

```bash
uv run pytest tests/api/test_orm_models.py -v
```

**Step 4: Commit**

```bash
git add api/orm_models.py tests/api/test_orm_models.py
git commit -m "feat: add SQLAlchemy ORM models (RawPost, Insight, Review)"
```

---

### Task 17: JSON → DB migration script

**Files:**
- Create: `api/migrate_json_to_db.py`

```python
# api/migrate_json_to_db.py
"""One-time migration: load data/insights/insights.json + review_log.json into DB."""

import json
from pathlib import Path
from api.db import Base, engine, SessionLocal
from api.orm_models import InsightORM, ReviewORM
from api.data import _parse_evidence, _normalize_status

INSIGHTS_PATH = Path("data/insights/insights.json")
REVIEW_LOG_PATH = Path("data/insights/review_log.json")


def migrate():
    Base.metadata.create_all(engine)
    db = SessionLocal()

    # Insights
    if INSIGHTS_PATH.exists():
        raw = json.loads(INSIGHTS_PATH.read_text())
        for item in raw:
            iid = str(item["topic_id"])
            if db.get(InsightORM, iid):
                continue  # skip if already migrated
            evidence = _parse_evidence(item.get("evidence", ""))
            db.add(InsightORM(
                id=iid,
                headline=item["headline"],
                category=item["category"],
                confidence=item["confidence"],
                summary=item["summary"],
                evidence=json.dumps(evidence),
                product_action=item["product_action"],
                volume_signal=item["volume_signal"],
                needs_human_review=item.get("needs_human_review", False),
                review_reason=item.get("review_reason"),
                canadian_context=item.get("canadian_context"),
                post_count=item.get("n_posts", 0),
            ))

    # Review log
    if REVIEW_LOG_PATH.exists():
        log = json.loads(REVIEW_LOG_PATH.read_text())
        for iid, entry in log.items():
            if db.query(ReviewORM).filter_by(insight_id=iid).first():
                continue
            db.add(ReviewORM(
                insight_id=iid,
                status=_normalize_status(entry.get("action", "pending")),
                note=entry.get("note", ""),
            ))

    db.commit()
    db.close()
    print("Migration complete.")


if __name__ == "__main__":
    migrate()
```

**Run migration:**
```bash
uv run python api/migrate_json_to_db.py
```

**Commit:**
```bash
git add api/migrate_json_to_db.py
git commit -m "feat: add JSON-to-DB migration script"
```

---

### Task 18: Update API routers to use DB (swap day)

This task runs **after** Phase 2A is complete and integration tested on JSON files. It swaps the data layer with no frontend changes required — the API contract stays identical.

**Files:**
- Modify: `api/routers/stats.py`
- Modify: `api/routers/insights.py`
- Modify: `api/routers/reviews.py`

**Step 1: Update `api/routers/stats.py`**

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from api.db import get_db
from api.models import Stats
from api.orm_models import InsightORM, ReviewORM

router = APIRouter()

@router.get("/api/stats", response_model=Stats)
def get_stats(db: Session = Depends(get_db)) -> Stats:
    insights = db.query(InsightORM).all()
    reviewed_ids = {
        r.insight_id for r in db.query(ReviewORM).all() if r.status != "pending"
    }
    return Stats(
        total_posts=sum(i.post_count for i in insights),
        total_insights=len(insights),
        pending_review=sum(1 for i in insights if i.id not in reviewed_ids),
        flagged_for_review=sum(1 for i in insights if i.needs_human_review),
    )
```

**Step 2: Update `api/routers/insights.py`**

```python
import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from api.db import get_db
from api.models import Insight
from api.orm_models import InsightORM

router = APIRouter()

def _to_model(orm: InsightORM) -> Insight:
    return Insight(
        id=orm.id,
        headline=orm.headline,
        category=orm.category,  # type: ignore[arg-type]
        confidence=orm.confidence,  # type: ignore[arg-type]
        summary=orm.summary,
        evidence=json.loads(orm.evidence),
        product_action=orm.product_action,
        volume_signal=orm.volume_signal,
        needs_human_review=orm.needs_human_review,
        review_reason=orm.review_reason,
        canadian_context=orm.canadian_context,
        post_count=orm.post_count,
    )

@router.get("/api/insights", response_model=list[Insight])
def list_insights(
    category: str | None = Query(None),
    confidence: str | None = Query(None),
    flagged: bool | None = Query(None),
    db: Session = Depends(get_db),
) -> list[Insight]:
    q = db.query(InsightORM)
    if category:   q = q.filter(InsightORM.category == category)
    if confidence: q = q.filter(InsightORM.confidence == confidence)
    if flagged is not None: q = q.filter(InsightORM.needs_human_review == flagged)
    return [_to_model(i) for i in q.all()]

@router.get("/api/insights/{insight_id}", response_model=Insight)
def get_insight(insight_id: str, db: Session = Depends(get_db)) -> Insight:
    orm = db.get(InsightORM, insight_id)
    if not orm:
        raise HTTPException(status_code=404, detail="Insight not found")
    return _to_model(orm)
```

**Step 3: Update `api/routers/reviews.py`**

```python
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from api.db import get_db
from api.models import Review, ReviewUpdate
from api.orm_models import ReviewORM

router = APIRouter()

def _to_model(orm: ReviewORM) -> Review:
    return Review(
        insight_id=orm.insight_id,
        status=orm.status,  # type: ignore[arg-type]
        note=orm.note,
        updated_at=orm.updated_at.isoformat() if orm.updated_at else "",
    )

@router.get("/api/reviews", response_model=list[Review])
def list_reviews(db: Session = Depends(get_db)) -> list[Review]:
    return [_to_model(r) for r in db.query(ReviewORM).all()]

@router.patch("/api/reviews/{insight_id}", response_model=Review)
def update_review(insight_id: str, update: ReviewUpdate, db: Session = Depends(get_db)) -> Review:
    orm = db.query(ReviewORM).filter_by(insight_id=insight_id).first()
    if orm:
        orm.status = update.status
        orm.note = update.note
        orm.updated_at = datetime.now()
    else:
        orm = ReviewORM(insight_id=insight_id, status=update.status, note=update.note)
        db.add(orm)
    db.commit()
    db.refresh(orm)
    return _to_model(orm)
```

**Step 4: Run full test suite**

```bash
uv run pytest tests/ -v
```

Note: The route tests use `monkeypatch` on `DEFAULT_DATA_DIR` which still works — add DB-backed tests if needed.

**Step 5: Commit**

```bash
git add api/routers/
git commit -m "feat: swap API routers from JSON files to SQLAlchemy DB"
```

---

## Phase 3: Integration + Cleanup

### Task 19: End-to-end smoke test

```bash
# 1. Migrate data
uv run python api/migrate_json_to_db.py

# 2. Start API
uv run uvicorn api.main:app --reload

# 3. In another terminal, build and verify
cd frontend && npm run build
curl http://localhost:8000/api/stats   # should return JSON
open http://localhost:8000             # should show Vue app
```

### Task 20: Retire Streamlit

```bash
# Remove from pyproject.toml hatch build packages:
# Before: packages = ["pipeline", "ui"]
# After:  packages = ["pipeline", "api"]

# Also remove streamlit and plotly from dependencies (now handled by frontend Chart.js)
uv sync
git add pyproject.toml uv.lock
git commit -m "chore: remove streamlit from build packages (retired)"
```

### Task 21: Final lint pass

```bash
uv run ruff check api/ && uv run ruff format api/
cd frontend && npm run build  # zero TypeScript errors
```

---

## Running both servers (dev)

```bash
# Terminal 1
uv run uvicorn api.main:app --reload --port 8000

# Terminal 2
cd frontend && npm run dev  # Vite at :5173, proxies /api → :8000
```

## Environment variables

```bash
# .env (Phase 2B+)
DATABASE_URL=sqlite:///./data/app.db        # local
# DATABASE_URL=postgresql://user:pw@host/db  # production
```
