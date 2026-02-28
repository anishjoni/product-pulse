# Wealthsimple AI Builder Program — Application Plan

## Context
**Deadline:** March 2, 11:59 PM EST (~5 days from Feb 25)
**Application requires:**
- 2-3 min demo video of a working system
- 500-word written explanation:
  - What human capabilities does the system enable?
  - What is AI responsible for?
  - What critical decision must remain human — and WHY?
  - What are the potential scaling failures?

---

## Selected Project: Community Intelligence Platform

### Concept
Aggregates public conversations from Reddit, Google Play/App Store reviews about Wealthsimple. AI classifies and synthesizes insights into:
- 🗺️ Roadmap opportunities (features users want)
- 🔥 Friction / pain points (recurring complaints)
- 🏆 Wins (things users love)
- 📈 Sentiment trends over time

**Elevator pitch:** "Wealthsimple has thousands of users telling them what to fix and what to build — in Reddit threads and app reviews. Most of that signal is lost. This platform finds it."

---

## Architecture

```
Data Collection Layer
├── PRAW (Reddit API) - free
│   └── r/PersonalFinanceCanada, r/wealthsimple, r/CanadianInvestor
├── google-play-scraper - free
│   └── Wealthsimple app reviews (Google Play)
├── app-store-scraper - free
│   └── Wealthsimple app reviews (Apple App Store)
└── Optional: Trustpilot scraper

Preprocessing Layer (Python / pandas)
├── Text cleaning, deduplication, date filtering
├── Filter to Wealthsimple-relevant content (keyword filter)
└── Language detection (English only)

ML Analysis Layer
├── BERTopic — topic modeling (auto-discovers topics)
├── Sentiment analysis (transformers HuggingFace pipeline)
└── Intent classification: roadmap / friction / win / other

LLM Synthesis Layer (Claude API — claude-sonnet-4-6)
├── Reads top posts per cluster
├── Writes plain-language summary per insight
├── Suggests specific product action per cluster
└── Flags ambiguous feedback for human review

Human Review Layer (Streamlit Dashboard)
├── Insight cards: topic + volume + sentiment + LLM summary
├── Filter by category (roadmap / friction / wins)
├── Approve → adds to product backlog | Dismiss → archive
└── Human annotates: "acted on", "known issue", "out of scope"
```

---

## Human-AI Division of Labor

| Layer | AI Handles | Human Must Control |
|-------|------------|-------------------|
| Collection | Automated ingestion from all sources | Deciding which sources to trust |
| Classification | Topic clustering, sentiment scoring | Overriding misclassified items |
| Synthesis | Summarizing patterns, writing insight cards | Interpreting nuance and context |
| Prioritization | Ranking by volume + sentiment | **Final roadmap decisions** |

### The One Critical Decision That Must Remain Human
**What feedback to act on — and what to dismiss.**

Why: AI measures volume and sentiment, but cannot determine:
- Whether a requested feature is regulatory/legal in Canada
- Whether it conflicts with Wealthsimple's strategic direction
- Whether loud voices represent actual user needs vs. a vocal minority
- Whether the feature has already been tried and failed
- The real cost and trade-offs of building it

The loudest online voices skew toward power users and complainers — the silent majority of satisfied users is invisible in this data. Only a human with full business context can bridge that gap.

### Potential Scaling Failures
1. **Feedback loop bias:** AI may amplify niche complaints over time if it learns from its own surfaced topics
2. **Gaming / brigading:** Coordinated posts could artificially inflate certain topics
3. **Platform blindspots:** Conversations on private Slack groups, forums, or email are invisible
4. **Language / cultural nuance:** Canadian financial terms (TFSA, FHSA, CRA) may be misclassified by general models
5. **Recency bias:** Viral posts skew short-term sentiment; longitudinal trends harder to detect

---

## Tech Stack
| Tool | Purpose | Cost |
|------|---------|------|
| PRAW | Reddit API wrapper | Free |
| google-play-scraper | Google Play reviews | Free |
| app-store-scraper | Apple App Store reviews | Free |
| BERTopic | Topic modeling | Free |
| transformers (HuggingFace) | Sentiment analysis | Free |
| Claude API (claude-sonnet-4-6) | Synthesis + insight generation | Minimal |
| Streamlit | Demo dashboard | Free |
| pandas | Data processing | Free |

**Total cost: ~$0 (only minor Claude API usage)**

---

## 5-Day Build Plan

| Day | Work |
|-----|------|
| Day 1 (Feb 25) | Data collection: PRAW + google-play-scraper + app-store-scraper |
| Day 2 (Feb 26) | Preprocessing, BERTopic topic modeling, sentiment analysis |
| Day 3 (Feb 27) | LLM synthesis layer (Claude API), insight card generation |
| Day 4 (Feb 28) | Streamlit dashboard, human review flow (approve/dismiss), polish |
| Day 5 (Mar 1) | Demo video recording, 500-word explanation, application narrative |
| Buffer (Mar 2) | Final review + submit before 11:59 PM EST |

---

## Demo Video Script (2-3 min)
1. **[0:00-0:20]** Hook: "Wealthsimple has thousands of users telling them what to fix and what to build. Most of that signal is lost. This platform finds it."
2. **[0:20-0:50]** Show live data pull (or pre-loaded recent data) from Reddit + App Store
3. **[0:50-1:30]** BERTopic clusters → AI synthesizes top 3 insight cards (roadmap, friction, win)
4. **[1:30-2:10]** Drill into one card — e.g., "47 posts mention confusion around TFSA over-contribution. Suggested action: add real-time TFSA room tracker." Human reviews → escalates to product.
5. **[2:10-2:40]** Human review flow — approve / dismiss / annotate
6. **[2:40-3:00]** Close: "AI finds the signal. Humans decide what to build."

---

## Application Narrative Themes
- **"Why Wealthsimple?"** — Demo itself is the answer: I've been listening to your users, here's what they're saying.
- **"What have you built?"** — This platform + prior DS/ML work
- **"What would you improve?"** — Proactive community listening; product team shouldn't need to manually browse Reddit

---

## Project File Structure
```
group_rider/
├── Initial plan.md
├── data/
│   └── raw/                     # Collected Reddit + App Store data
├── pipeline/
│   ├── collect_reddit.py        # PRAW collector
│   ├── collect_appstore.py      # Google Play + App Store scraper
│   ├── preprocess.py            # Cleaning, dedup, filtering
│   ├── topic_model.py           # BERTopic pipeline
│   ├── sentiment.py             # HuggingFace sentiment
│   └── synthesize.py            # Claude API insight generation
├── ui/
│   └── app.py                   # Streamlit dashboard
├── requirements.txt
└── README.md
```
