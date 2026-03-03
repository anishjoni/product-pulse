# Phase 7 — Deployment

## Goal
The app should run locally with a single command for development, and be deployable to
Modal (backend) + Vercel (frontend) for a hosted demo URL.

## Agents Involved
- Backend (Modal deployment, environment config)
- Frontend (Vercel deployment)
- QA (smoke test both environments)

---

## Local Development

### Prerequisites
- Python 3.11+
- Node.js 18+
- Ollama installed locally (for LLM fallback): `curl -fsSL https://ollama.ai/install.sh | sh`
- Pull llama3 model: `ollama pull llama3`

### Setup
```bash
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # fill in REDDIT_CLIENT_ID, ANTHROPIC_API_KEY, etc.
python src/db/init_db.py       # creates SQLite DB + runs seed
uvicorn src.api.main:app --reload --port 8000

# Frontend
cd frontend
npm install
cp .env.local.example .env.local   # set NEXT_PUBLIC_API_BASE=http://localhost:8000
npm run dev                         # runs on localhost:3000
```

### One-command local start (docker-compose for demo)
```yaml
# docker-compose.yml
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    env_file: ./backend/.env
    volumes: ["./data:/app/data"]   # persist SQLite DB

  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    environment:
      NEXT_PUBLIC_API_BASE: http://localhost:8000
    depends_on: [backend]
```

---

## Modal Deployment (Backend)

Modal is used to host the FastAPI backend as a serverless app.

### modal_app.py
```python
import modal

app = modal.App("product-pulse-backend")
image = modal.Image.debian_slim().pip_install_from_requirements("requirements.txt")

@app.function(
    image=image,
    secrets=[modal.Secret.from_name("product-pulse-secrets")],
    volumes={"/app/data": modal.Volume.from_name("product-pulse-db", create_if_missing=True)}
)
@modal.asgi_app()
def fastapi_app():
    from src.api.main import app as fastapi_app
    return fastapi_app
```

### Modal Secrets to configure
Set these in the Modal dashboard under a secret named `product-pulse-secrets`:
```
REDDIT_CLIENT_ID
REDDIT_CLIENT_SECRET
REDDIT_USER_AGENT
YOUTUBE_API_KEY
ANTHROPIC_API_KEY
DATABASE_URL=sqlite:////app/data/pulse.db
CORS_ORIGINS=https://<your-vercel-app>.vercel.app
```

### Deploy command
```bash
modal deploy modal_app.py
```

### Note on Ollama fallback on Modal
Ollama cannot run on Modal's default containers. On Modal deployment:
- If Claude quota is exhausted, log a warning and skip classification (mark as `pending`)
- A separate nightly Modal cron job retries all `pending` items when quota resets
- This is acceptable for a demo — classify what we can, retry the rest

---

## Vercel Deployment (Frontend)

```bash
cd frontend
npx vercel --prod
# Set environment variable in Vercel dashboard:
# NEXT_PUBLIC_API_BASE = https://<your-modal-app>.modal.run
```

### CORS
Once frontend Vercel URL is known, update `CORS_ORIGINS` in Modal secrets and redeploy backend.

---

## Project Directory Structure (Final)
```
wealthsimple_pulse/
  backend/
    src/
      api/          # FastAPI app
      ingestion/    # scrapers
      llm/          # classification pipeline
      analysis/     # trend engine
      db/           # repositories, init_db, seed
    modal_app.py
    requirements.txt
    .env.example
    Dockerfile
  frontend/
    src/
      app/          # Next.js app router
      components/   # UI components
      lib/          # API client, utils
    package.json
    .env.local.example
  docker-compose.yml
  claude_plans/     # this folder — agent source of truth
  directives/       # agent-generated architecture notes
  execution/        # deterministic scripts agents write
  CLAUDE.md
```

## Acceptance Criteria
- [ ] `docker-compose up` starts both services, frontend loads at localhost:3000
- [ ] `modal deploy` completes without errors
- [ ] Modal backend URL responds to `GET /products`
- [ ] Vercel frontend loads and connects to Modal backend
- [ ] Manual scout run works on the hosted version
- [ ] SQLite DB persists across Modal redeployments (via Modal Volume)
