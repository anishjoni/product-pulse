# Product Pulse — Claude Code Instructions

## What We Are Building
A configurable community feedback aggregator for product teams. Scrapes Reddit + YouTube,
classifies posts via LLM, detects trending topics, and presents a pulse dashboard.
See `claude_plans/PRD.md` for the full brief.

## Agent Team
This project uses Claude Code agent teams. Enable with:
```json
// .claude/settings.json
{ "claudeCodeExperimentalAgentTeams": 1 }
```

Team: **Team Lead/Devil's Advocate**, **Backend Developer**, **Frontend Developer**, **QA Engineer**
Roles and execution order: `claude_plans/08_agent_roles.md`

## Directory Structure
```
claude_plans/    ← ALL requirements live here. Read before writing any code.
directives/      ← Agents write architecture notes and decisions here.
execution/       ← Agents write deterministic scripts here (init, test, deploy).
backend/         ← Python/FastAPI application
frontend/        ← Next.js 14 application
```

## Rules
- **Read `claude_plans/` before writing any code**
- **No secrets in code** — environment variables only
- **Polars, not pandas** — backend data manipulation
- **Shadcn/UI + Recharts** — frontend only, no other component/chart libs
- **Acceptance criteria = definition of done** — check the plan file checkboxes
- **Write scripts to `execution/`** — prefer deterministic code over LLM-at-runtime

## Tech Stack
- Backend: Python 3.11, FastAPI, Polars, SQLite/PostgreSQL, APScheduler
- LLM: Gemini 2.0 Flash (primary, free tier), Ollama llama3 (fallback)
- Frontend: Next.js 14, TypeScript, Shadcn/UI, Tailwind, Recharts
- Deployment: Docker Compose (local), Modal (backend hosted), Vercel (frontend hosted)
