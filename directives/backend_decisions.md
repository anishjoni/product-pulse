# Backend Architecture Decisions — Phase 1

## Why sqlite3 stdlib instead of SQLAlchemy

SQLAlchemy is a powerful ORM but introduces a meaningful dependency surface
(the core package plus optional extensions), a non-trivial learning curve for
contributors unfamiliar with it, and runtime overhead that is unnecessary for a
demo application whose data access patterns are simple and well-understood.

Using Python's built-in `sqlite3` module keeps the dependency list lean, makes
the data-access code explicit and easy to read without any ORM magic, and
removes one potential source of incompatibility across Python versions. Every
query is plain SQL, which is easier to audit and optimise.

## Why seed is idempotent (slug unique check)

The `seed()` function is called on every application startup alongside
`init_db()`. Making it idempotent (by checking whether a product with the
target slug already exists before inserting) means:

1. The server can restart freely without accumulating duplicate rows.
2. Developers can run `python -m src.db.seed` directly at any time without
   worrying about state.
3. CI/CD pipelines that re-run startup steps on every deploy are safe by
   default.

The slug column is the natural idempotency key because it is a human-readable,
URL-safe identifier that is defined in the seed data itself and is enforced as
UNIQUE at the database level.

## Why product config is stored in the database, not in env vars or config files

Environment variables and config files are baked into the deployment artifact
or set at startup time. Any change requires either a redeployment or a server
restart, which is friction-heavy and not operator-friendly.

Storing product configuration (names, slugs, keywords, sources) in the SQLite
database means:

1. **Survives deploys** — the database file persists across container restarts
   and code updates; a new deployment does not wipe product configuration.
2. **Editable via UI** — the `PUT /products/{id}` endpoint (and future admin
   UI) lets operators add keywords or toggle sources at runtime without touching
   any infrastructure.
3. **Single source of truth** — all agents (scout, classifier, trend analyser)
   read product config from the same DB, preventing config drift between
   components.

---

# Backend Architecture Decisions — Phase 2

## Why posts AND comments are both ingested from Reddit

A Reddit post's title and selftext alone are often terse and lack the nuance
needed for reliable LLM classification. The real signal frequently lives in
the comment thread — bug reproducers, workaround suggestions, feature debates,
and user sentiment. Ingesting up to 10 top-level comments per post multiplies
the signal per API call without meaningfully increasing Reddit quota usage
(PRAW handles comment fetching as part of the same post object), while also
giving the trend analyser more data points to detect emerging topics. The
`UNIQUE(source, external_id)` constraint guarantees comments are not
double-counted on subsequent runs.

## Why YouTube API errors are silently caught (not re-raised)

YouTube's free tier is limited to 10,000 units per day. A single `search.list`
call costs 100 units, meaning a single product with multiple YouTube sources
can exhaust the daily quota quickly in a busy environment. If the YouTube
scraper raised exceptions on quota exhaustion or API errors, a single YouTube
failure would abort the entire scout run and leave no Reddit data persisted for
the day — an all-or-nothing failure that is worse than partial data. Logging a
warning and returning an empty list lets the Reddit data reach the database
regardless of YouTube quota state, and the scout run is still marked
`completed` with an accurate `items_fetched` count. Operators can inspect logs
to identify YouTube quota issues without losing Reddit coverage.

## Why scout_runs tracks items_fetched and items_classified as separate counters

Ingestion (Phase 2) and classification (Phase 3) are deliberately decoupled
pipeline stages. A scout run writes raw text to `raw_feedback`, then returns.
Classification is a separate, potentially expensive LLM step that runs
asynchronously (or on-demand) after ingestion completes. Tracking
`items_fetched` at the end of the scout run gives operators an immediate count
of how many new items arrived, even before any LLM work begins.
`items_classified` starts at 0 and is incremented by the Phase 3 classifier as
it processes each item. This separation means:

1. Scout run status (`completed` / `failed`) reflects ingestion health only —
   a classification failure does not retroactively mark the scout run as failed.
2. The dashboard can show "X items fetched, Y classified so far" for
   transparency into pipeline progress.
3. Re-running classification on a completed scout run (e.g. after a model
   upgrade) is trivial — query `raw_feedback` for rows with no corresponding
   `classified_feedback` row using `RawFeedbackRepository.get_unclassified()`.

---

# Backend Architecture Decisions — Phase 3

## Why classification runs inside the scout run (not a separate scheduled job)

For a demo application the simplest mental model wins: one API call triggers
one scout run, which fetches data AND classifies it. Operators get a single
status endpoint that tells the full story of what happened. A separate
classification job would require an additional scheduler entry, a separate
status table, and a more complex UI to correlate ingestion with classification.
The tradeoff is that a scout run takes longer (LLM latency per item), but for
a demo with 10–50 items per run this is acceptable. If volume grows, the
classification step can be extracted into a background task without changing
the repository interface.

## Why content is truncated to 2000 characters before sending to the LLM

Gemini 2.0 Flash has a generous context window, but the free tier has
per-request token limits that can cause errors on very long Reddit threads or
YouTube comment dumps. Truncating to 2000 characters (roughly 400–500 tokens
of English text) keeps every request safely within the free-tier envelope,
reduces latency, and focuses the model on the most relevant part of the post.
The signal needed for category classification is almost always present in the
first 2000 characters; later content tends to be replies, tangents, or
repetition.

## Why failed classifications are stored with status='failed' rather than dropped

Dropping failed items would make failures invisible: operators could not
distinguish "this item was never classified" from "we tried and it failed".
Storing a placeholder row with classification_status='failed' means:

1. Observability — a simple SQL query (`SELECT COUNT(*) WHERE
   classification_status = 'failed'`) surfaces pipeline health without
   scanning logs.
2. Retryability — a future maintenance script or admin endpoint can query for
   failed rows and re-submit them to the LLM without re-running the full scout.
3. Completeness — items_classified on the scout run reflects how many items
   were processed (attempted), not just how many succeeded, giving an honest
   picture of run throughput.

---

# Backend Architecture Decisions — Phase 7

## Why the Modal cron is separate from the embedded APScheduler

APScheduler runs inside the FastAPI process. On Modal's serverless platform,
containers scale to zero when there is no HTTP traffic, which means APScheduler
stops and misses any scheduled runs that happen while no container is alive.

Modal's own `schedule=modal.Cron(...)` decorator solves this: Modal itself
invokes the function at the configured time regardless of whether any web
containers are running. The two mechanisms coexist cleanly:

1. `DISABLE_SCHEDULER=1` is injected by modal_app.py — main.py checks this
   env var at startup and skips launching APScheduler, so there is no
   double-scheduling.
2. Locally (no DISABLE_SCHEDULER), APScheduler runs as before.

## Why SQLite + Modal Volume instead of a managed database

A managed PostgreSQL (e.g. Neon, Supabase, Railway) would require a paid plan
or introduces another signup/configuration step for a demo. Modal Volumes
provide a persistent network filesystem that survives container restarts and
redeployments, making SQLite an acceptable choice for single-tenant demo
traffic. Migration to PostgreSQL is a one-line DATABASE_URL change; the
application code is already agnostic (sqlite3 vs psycopg2 is the only delta,
and only in database.py).

## Why output: standalone for the Next.js Docker image

Next.js `output: "standalone"` produces a self-contained `.next/standalone`
directory that includes only the server-side code needed to run the app, with
`node_modules` tree-shaken down to the actual runtime dependencies. This
reduces the final Docker image size by ~70% compared to copying the full
`node_modules` tree, and avoids having to re-run `npm install` in the runner
stage. The tradeoff is that the build step takes slightly longer, which is
acceptable in a CI/CD pipeline but not in development (where `npm run dev` is
used directly).

---

# Backend Architecture Decisions — Phase 4

## Why Polars for trend aggregation

Trend analysis requires grouping thousands of normalised topic tokens by window
and category. Pure Python loops over thousands of rows are O(n) per grouping
operation with significant per-element overhead. Polars uses Apache Arrow memory
layout and vectorised SIMD operations under the hood, making group_by + agg
operations 10–100× faster on typical data sizes than equivalent list-iteration.
The Polars API also makes the pipeline readable — each transformation is a named
expression chain — which matters for maintainability. Using pandas instead of
Polars would violate the project's explicit tech-stack rule and add a heavier
dependency with no benefit for this use case.

## Why minimum 3 mentions threshold (not 1 or 2)

A threshold of 1 or 2 mentions makes 100–200% spikes trivial to trigger: a
single user posting twice about any topic would surface it as a "trend". That
produces noise, not signal. The 3-mention floor ensures a topic has been
discussed by at least a handful of distinct conversations in the current window
before it qualifies. Combined with the 50% growth requirement this means the
smallest qualifying scenario is 3 current / 0 previous (new topic entirely) or
3 current / 2 previous (+50%). Both represent genuine emerging interest rather
than random variance from thin data.

## Why trends are recomputed per scout run (not cached with a TTL)

Recomputing on every scout run is simple, deterministic, and self-healing:

1. Idempotent — running compute_trends() twice for the same product at the same
   time produces identical results; there is no accumulation of stale state.
2. Always fresh — trends reflect the data that was just classified in the
   current run, so the dashboard is never more than one run behind.
3. No invalidation logic needed — a cache requires invalidation rules that
   interact with scout run timing, product configuration changes, and manual
   recomputes. Removing that complexity is worth the small CPU cost of a Polars
   aggregation over a few thousand rows.
4. Failure isolation — trend computation errors are caught separately from
   ingestion/classification errors and logged as non-fatal, so a transient LLM
   or DB issue never prevents ingestion data from being saved.

