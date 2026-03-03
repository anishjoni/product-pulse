# Product Pulse — Product Requirements Document

## Problem Statement

For any consumer product (e.g. Wealthsimple Trade, Xbox), there is a constant stream of real user
feedback scattered across Reddit, YouTube, and social platforms. Product teams currently have no
automated way to aggregate, categorize, and surface these signals in real time. Critical insights —
a feature loved by thousands, a bug spiking in complaints, a community expectation following a
major announcement — get missed or discovered too late.

## Solution

A configurable web application that:
1. Continuously ingests community feedback from Reddit and YouTube (Twitter/X as Phase 2)
2. Classifies every post/comment via LLM into actionable categories
3. Detects emerging trends and topic spikes (e.g. a 200% rise in "options spreads" mentions)
4. Presents a clean internal dashboard for product teams — no noise, just signal

## Target User

Internal product managers, growth leads, and community teams who need to stay informed without
manually reading hundreds of Reddit threads or YouTube comments each day.

## Non-Goals

- No public-facing features
- No auto-posting or response drafting to social platforms
- No real-time stream processing (scheduled batch is sufficient)
- No user authentication beyond a simple API key gate for the demo

## Core Concepts

### Product
A configured target (e.g. "Wealthsimple Trade", "Xbox"). Each product has:
- A name and description
- A list of tracked keywords/phrases
- A list of subreddits to monitor
- A list of YouTube channel IDs or search terms to monitor
- Source enable/disable toggles

### Scout Run
A scheduled or manually triggered job that:
- Fetches the latest N posts/comments per source for a product
- Sends each item to the LLM for classification
- Stores raw + classified results
- Triggers trend recalculation

### Category
Every piece of feedback is assigned exactly one category:
- **Feature Request** — user wants something added or changed ("I wish it showed spreads as a single contract")
- **Bug Report** — user reports something broken or incorrect
- **Complaint** — negative sentiment about existing behaviour, pricing, UX
- **Praise** — positive sentiment, things working well
- **General Discussion** — community conversation, announcements, expectations (e.g. new CEO, market events)

### Trend
A topic or keyword cluster that has increased in mention frequency by ≥ 50% in the current
period vs. the previous comparable period. Displayed as a ranked bar chart.

## Success Metrics (Demo)

- Correctly classifies ≥ 85% of test feedback items by category
- Detects a simulated 200% spike in "options spreads" within one scout run
- Dashboard loads in < 2 seconds
- Scout run for one product completes in < 60 seconds with rate limiting applied

## Tech Stack

| Layer | Technology |
|---|---|
| Backend API | Python + FastAPI |
| Data Processing | Polars |
| Storage | SQLite (dev) / PostgreSQL (prod) |
| Scheduling | APScheduler (embedded in FastAPI) |
| Frontend | Next.js 14 + Shadcn/UI + Recharts |
| LLM Primary | Gemini 2.0 Flash (free tier: 15 RPM, 1,500 req/day) |
| LLM Fallback | Ollama + llama3 (local, when Gemini quota exhausted) |
| Deployment | Local dev + Modal (hosted) |

## Phases

| # | Phase | Owner |
|---|---|---|
| 1 | Product Configuration | Backend |
| 2 | Data Ingestion (Reddit + YouTube) | Backend |
| 3 | LLM Processing Pipeline | Backend |
| 4 | Data Storage & Schema | Backend |
| 5 | Trend Analysis Engine | Backend |
| 6 | REST API Layer | Backend |
| 7 | Frontend Dashboard | Frontend |
| 8 | Deployment (Local + Modal) | Backend + Frontend |
| 9 | Agent Roles & Coordination | Team Lead |
