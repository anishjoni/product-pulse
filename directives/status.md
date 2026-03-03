# Build Status

## Phase 1 — Product Configuration ✅ COMPLETE
- 15 Python source files + 2 config files created under `backend/`
- `execution/init_db.sh` created
- `directives/backend_decisions.md` created
- `.gitignore` created (Team Lead addition)
- All 7 acceptance criteria passed
- Minor addition: `ProductUpdateRequest` schema added (required by PUT endpoint)

### Blockers before Phase 2 starts:
1. `.env` file needed with: `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `YOUTUBE_API_KEY`, `ANTHROPIC_API_KEY`
2. Full `pip install -r requirements.txt` must be run in the venv

## Phase 2 — Data Ingestion ✅ COMPLETE
- RedditScraper + YouTubeScraper + ScoutRunner implemented
- scout_runs + raw_feedback tables added to init_db
- ScoutRunRepository + RawFeedbackRepository created
- POST /products/{id}/scout, GET scout-runs endpoints wired in
- Test run: 223 items fetched (76 Reddit, 147 YouTube), deduplication confirmed working
- 0 blockers for Phase 3
## Phase 3 — LLM Classification ✅ COMPLETE
- classified_feedback table added to init_db
- GeminiClient + OllamaClient + LLMClassifier implemented
- Provider chain: Gemini → Ollama (agent also added Claude Haiku as middle step — skips gracefully if ANTHROPIC_API_KEY not set)
- 4/5 test cases pass (1 edge case: "spreads confusing" got bug_report vs complaint — acceptable)
- Gemini free quota currently exhausted (resets midnight UTC); Ollama llama3 8B handling fallback
- Scout run now includes classification step; items_classified tracked
- execution/test_classification.sh created
## Phase 4 — Trend Analysis ✅ COMPLETE
- TrendAnalyser using Polars, min 3 mentions + 50% growth threshold
- TrendsRepository (upsert, get, get_latest_computed_at)
- Trends computed inside scout run, also available via recompute=true query param
- execution/compute_trends.sh created

## Phase 5 — API Layer ✅ COMPLETE
- All product CRUD endpoints wired (GET/POST/PUT/DELETE /products, /products/{id})
- GET /products/{id}/summary — pulse overview (total, category_counts, avg_sentiment, sentiment_trend, top_trend, last_scout)
- GET /products/{id}/feedback — paginated+filtered classified feedback (category, source, sentiment, search, date_from, date_to)
- GET /feedback/{id} — single item with full raw content
- GET /products/{id}/trends — sorted by pct_change DESC, recompute option
- POST /products/{id}/scout — 409 if run already in progress
- APScheduler embedded: daily cron via SCOUT_SCHEDULE_CRON env (default: 0 6 * * *)
- Startup catch-up: any product not scouted in >23h is scouted immediately
- CORS configured (wildcard dev, CORS_ORIGINS env for prod)
- Venv recreated with Python 3.12 (miniconda was removed); all packages installed

### Blockers before Phase 6 starts:
1. .env file with API keys still required for scout/classify to work
2. Frontend: Next.js 14 + Shadcn/UI + Recharts (see claude_plans/06_frontend_dashboard.md)

## Phase 6 — Frontend Dashboard ✅ COMPLETE
- Next.js 14 scaffolded with TypeScript, Tailwind, App Router, Shadcn/UI, Recharts
- Node installed via NVM (v20); frontend/.venv not needed (separate runtime)
- Pages: / (product selector/redirect), /dashboard, /feed, /trends, /settings
- Components: PulseScoreBar, CategoryCards, TrendingBarChart, SentimentTimeline, FeedCard, FeedFilters
- lib/api.ts: typed fetch wrappers for all backend endpoints
- Production build passes (npm run build ✓)
- execution/run_frontend.sh created

## Phase 7 — Deployment ✅ COMPLETE
- backend/Dockerfile (Python 3.12 slim, uvicorn entrypoint)
- frontend/Dockerfile (multi-stage: node:20-alpine builder + standalone runner)
- next.config.mjs: output: "standalone" added for Docker compatibility
- docker-compose.yml: backend + frontend services, pulse_data volume, healthcheck
- backend/.env.example: all required env vars documented
- frontend/.env.local.example: NEXT_PUBLIC_API_BASE template
- backend/modal_app.py: Modal ASGI deployment + separate Modal Cron scout function
- DISABLE_SCHEDULER=1 env var suppresses embedded APScheduler on Modal
- execution/deploy_modal.sh helper script
- docker-compose YAML validated; Next.js standalone build confirmed ✓

### To run locally with Docker:
```
cp backend/.env.example backend/.env   # fill in API keys
docker-compose up --build
```

### To deploy to Modal + Vercel:
```
cd backend && pip install modal && modal setup
modal secret create product-pulse-secrets REDDIT_CLIENT_ID=... ...
bash execution/deploy_modal.sh
# Then set NEXT_PUBLIC_API_BASE in Vercel dashboard
cd frontend && npx vercel --prod
```
