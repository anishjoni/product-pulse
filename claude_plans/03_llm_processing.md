# Phase 3 — LLM Classification Pipeline

## Goal
Send each raw feedback item to an LLM for classification. Store structured results.
Use Gemini 2.0 Flash as primary (free tier: 15 RPM, 1,500 req/day). Fall back to local
Ollama when Gemini quota is exhausted or the API returns a rate limit error.

## Agents Involved
- Backend (implementation)
- Devil's Advocate (review prompt quality, hallucination risk, fallback logic)

## Categories
Every item is classified into exactly one:
- `feature_request` — user wants something added or improved
- `bug_report` — user reports something broken
- `complaint` — negative sentiment about existing behaviour
- `praise` — positive sentiment, things working well
- `general_discussion` — announcements, community expectations, neutral commentary

## LLM Output Schema (JSON)
```json
{
  "category": "feature_request",
  "sentiment": 0.3,
  "summary": "User wants options spreads displayed as a single net position rather than two legs",
  "topics": ["options", "spreads", "UI", "portfolio view"],
  "confidence": 0.92
}
```

Fields:
- `category`: one of the five values above
- `sentiment`: float from -1.0 (very negative) to 1.0 (very positive)
- `summary`: one sentence, max 120 chars, written in third person
- `topics`: 2–5 keywords extracted from the content (for trend analysis)
- `confidence`: float 0.0–1.0, how confident the model is in the classification

## Classification Prompt

```
You are a product intelligence analyst. Classify the following community post about {product_name}.

Return ONLY valid JSON matching this schema — no markdown, no code fences, no explanation:
{
  "category": "<feature_request|bug_report|complaint|praise|general_discussion>",
  "sentiment": <float -1.0 to 1.0>,
  "summary": "<one sentence, max 120 chars, third person>",
  "topics": ["<keyword>", ...],
  "confidence": <float 0.0 to 1.0>
}

Context about {product_name}: {product_description}
Keywords associated with this product: {keywords_csv}

Post/comment to classify:
---
{content}
---
```

## LLM Provider Strategy

```python
class LLMClassifier:
    def classify(self, item: RawFeedbackItem, product: Product) -> ClassificationResult:
        try:
            return self._classify_with_gemini(item, product)
        except (GeminiQuotaError, GeminiRateLimitError) as e:
            logger.warning(f"Gemini quota/rate limit hit ({e}), falling back to Ollama")
            return self._classify_with_ollama(item, product)

    def _classify_with_gemini(self, item, product) -> ClassificationResult:
        # Use google-generativeai SDK
        # Model: gemini-2.0-flash
        # generation_config: temperature=0.1 (low temp for consistent classification)
        # Parse JSON from response.text — strip markdown fences if present

    def _classify_with_ollama(self, item, product) -> ClassificationResult:
        # POST to http://localhost:11434/api/generate
        # Model: read from OLLAMA_MODEL env var (default: llama3)
        # Same prompt, parse JSON from response
```

## Gemini Client (src/llm/gemini_client.py)

```python
import os
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, TooManyRequests

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

class GeminiClient:
    def __init__(self):
        self.model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            generation_config={"temperature": 0.1, "response_mime_type": "application/json"}
        )

    def generate(self, prompt: str) -> str:
        response = self.model.generate_content(prompt)
        return response.text

# Re-export exceptions for use in classifier.py
GeminiQuotaError = ResourceExhausted
GeminiRateLimitError = TooManyRequests
```

Note: Setting `response_mime_type: "application/json"` forces Gemini 2.0 Flash to return
valid JSON without markdown fences — no post-processing needed.

## Error Handling
- If JSON parsing fails: retry once with explicit instruction "Return ONLY the JSON object, no markdown"
- If second attempt fails: mark item as `classification_status = 'failed'`, do not crash the run
- Log provider used per item (`gemini` | `ollama`) for observability
- If Ollama is not running: log warning and mark as failed (not a crash)
- Gemini free tier: 15 RPM — add a 4-second sleep between requests to stay safe

## Data Model

```sql
CREATE TABLE classified_feedback (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    raw_feedback_id       INTEGER NOT NULL UNIQUE REFERENCES raw_feedback(id),
    category              TEXT NOT NULL,
    sentiment             REAL NOT NULL,
    summary               TEXT NOT NULL,
    topics                TEXT NOT NULL,   -- JSON array: '["options","spreads"]'
    confidence            REAL NOT NULL,
    llm_provider          TEXT NOT NULL,   -- "gemini" | "ollama"
    classified_at         TEXT NOT NULL DEFAULT (datetime('now')),
    classification_status TEXT NOT NULL DEFAULT 'success'  -- "success" | "failed"
);
```

## File Structure
```
src/
  llm/
    __init__.py
    classifier.py           # LLMClassifier class
    prompt_builder.py       # builds the classification prompt
    gemini_client.py        # thin wrapper around google-generativeai SDK
    ollama_client.py        # thin wrapper around Ollama HTTP API
  db/
    repositories/
      classified_feedback_repository.py
```

## Environment Variables Required
```
GEMINI_API_KEY=
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
CLASSIFIER_DELAY_SECONDS=4   # sleep between Gemini requests (free tier RPM safety)
```

## Processing Flow (called by scout_runner.py)
1. Fetch all `raw_feedback` items for this scout run with no corresponding `classified_feedback`
2. For each item: build prompt → call LLMClassifier → store result → sleep CLASSIFIER_DELAY_SECONDS
3. After all items: update `scout_run.items_classified`
4. Batch size: process 10 items at a time (not all at once) to manage memory

## Acceptance Criteria
- [ ] Classification returns valid JSON for a Reddit post about Wealthsimple
- [ ] A post "app crashed when I opened options chain" is classified as bug_report
- [ ] A post "wish they had fractional shares for ETFs" is classified as feature_request
- [ ] A post "love the new UI update" is classified as praise
- [ ] A post "Phil Spencer stepping down as Xbox CEO" is classified as general_discussion
- [ ] When GEMINI_API_KEY quota is exhausted, falls back to Ollama without crashing
- [ ] Failed classifications are stored with status 'failed', not lost
- [ ] `llm_provider` field is correctly recorded as "gemini" or "ollama"
- [ ] Rate limit delay is applied between Gemini requests
