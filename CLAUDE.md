# Wealthsimple Community Intelligence Platform — Dev Standards

## Package Management
- **Always use `uv`** — never `pip install` directly
- Install deps: `uv sync`
- Add a dep: `uv add <package>`
- Dev deps live under `[tool.uv]` in `pyproject.toml`

## Data Processing
- **Prefer `polars`** for all DataFrame work
- Use `pl.read_ndjson` / `df.write_ndjson` for all pipeline data files (`.ndjson` format)
- Fall back to `pandas` only when a library requires it 
- Avoid `.apply()` in polars — use expressions or `map_elements` only when necessary

## Logging
- **Always use `loguru`** — never `logging.basicConfig`
- Import from the central config: `from pipeline.config import logger`
- Use `logger.success()` for pipeline step completions
- Terminal output is colored automatically; full debug logs go to `logs/`

## Code Style
- **Ruff** for linting and formatting 
- Line length: 100 chars (configured in `pyproject.toml`)
- Python 3.11+ — use `match`, `X | Y` union types, `list[str]` not `List[str]`

## Environment / Config
- All env vars go through `pipeline/config.py` — use `require_env()` for required vars, `optional_env()` for optional ones with defaults
- **Never hardcode API keys** — always use `.env` (gitignored)

## LLM / AI
- Synthesis layer uses **Google Gemini API** (`gemini-2.0-flash`) — free tier
- Get a key at https://aistudio.google.com → "Get API key", set as `GEMINI_API_KEY`
- Model constant lives in `pipeline/config.py` as `GEMINI_MODEL`

## Data Viz / UI
- Color palette (defined in `ui/app.py`):
  - Roadmap: `#2563EB` (deep blue)
  - Friction: `#EF4444` (red)
  - Win: `#059669` (teal-green)
  - Other: `#6B7280` (gray)
- **Don't crowd charts** — one focused chart per section, clean KPI tiles
- Streamlit dashboard runs with demo data by default (no pipeline run required)

## Pipeline Data Flow
```
data/raw/*.ndjson          ← collect_reddit.py, collect_appstore.py
data/processed/cleaned.ndjson     ← preprocess.py
data/processed/with_topics.ndjson ← topic_model.py
data/processed/with_sentiment.ndjson ← sentiment.py
data/insights/insights.json       ← synthesize.py
```

## CI
- GitHub Actions runs on push to `main` / `dev`: ruff lint → ruff format check → pytest
- Secrets needed: `GEMINI_API_KEY`, `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`
