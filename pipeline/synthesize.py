"""
LLM Synthesis Layer — Ollama (local models).
Reads top posts per topic cluster and generates structured insight cards.

Requires Ollama running locally with a model pulled, e.g.:
    ollama pull qwen3-coder:30b

Usage:
    uv run python pipeline/synthesize.py
"""

import json
import re
import time
from collections import Counter

import ollama
import polars as pl

from pipeline.config import (
    INSIGHTS_DIR,
    PROCESSED_DIR,
    logger,
)

MAX_POSTS_PER_TOPIC = 10
MIN_TOPIC_SIZE = 5
MAX_TOPICS = 30

OLLAMA_MODEL = "qwen3-coder:30b"


def _ollama_host() -> str:
    """Detect Ollama host: try localhost first, fall back to WSL2 Windows gateway."""
    import subprocess

    import httpx

    for host in ["http://localhost:11434"]:
        try:
            httpx.get(f"{host}/api/tags", timeout=2)
            return host
        except Exception:
            pass
    # WSL2: Windows host is the default gateway
    try:
        result = subprocess.run(
            ["ip", "route"], capture_output=True, text=True, timeout=3
        )
        for line in result.stdout.splitlines():
            if "default" in line:
                gw = line.split()[2]
                return f"http://{gw}:11434"
    except Exception:
        pass
    return "http://localhost:11434"


OLLAMA_HOST = _ollama_host()

SYSTEM_PROMPT = """You are a senior product intelligence analyst at Wealthsimple.
Your job is to read a cluster of user feedback posts and synthesize them into a structured insight card
that a product manager can act on immediately.

You understand the Canadian financial context: TFSAs, RRSPs, FHSAs, CRA rules, and the competitive
landscape (Questrade, RBC Direct Investing, etc.).

Always be specific, grounded in the actual feedback, and honest about uncertainty.
Never invent features or problems not mentioned in the data.
Respond with ONLY valid JSON — no markdown fences, no commentary, no thinking."""


def build_prompt(topic_id: int, topic_words: str, posts: list[dict]) -> str:
    posts_text = "\n\n".join(
        f"[{i + 1}] Source: {p.get('source')} | "
        f"Score/Rating: {p.get('score') or p.get('rating', 'N/A')} | "
        f"Date: {str(p.get('created_utc', ''))[:10]}\n{str(p['full_text'])[:800]}"
        for i, p in enumerate(posts)
    )

    return f"""Analyze this cluster of {len(posts)} user feedback posts about Wealthsimple.

TOPIC CLUSTER #{topic_id}
Auto-detected keywords: {topic_words}

USER POSTS:
{posts_text}

Generate a structured insight card in the following JSON format (respond with ONLY valid JSON, no markdown fences):
{{
  "topic_id": {topic_id},
  "headline": "Short, punchy 8-12 word summary of what users are saying",
  "category": "roadmap|friction|win|other",
  "confidence": "high|medium|low",
  "summary": "2-3 sentences grounded in the posts. What are users experiencing or asking for?",
  "evidence": "1-2 direct quotes or paraphrases that best illustrate the theme",
  "product_action": "Specific, actionable suggestion. E.g. 'Add real-time TFSA room tracker in account overview.'",
  "volume_signal": "How strong is this signal? e.g. '47 posts, recurring over 6 months'",
  "needs_human_review": true,
  "review_reason": "Why this needs human attention, or null",
  "canadian_context": "Canadian-specific considerations (regulatory, TFSA/RRSP/FHSA rules) or null"
}}"""


def strip_thinking(text: str) -> str:
    """Remove <think>...</think> blocks emitted by reasoning models like qwen3."""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def synthesize_topic(
    client: ollama.Client,
    topic_id: int,
    topic_words: str,
    posts: list[dict],
    retries: int = 2,
) -> dict | None:
    prompt = build_prompt(topic_id, topic_words, posts)

    for attempt in range(retries + 1):
        try:
            response = client.chat(
                model=OLLAMA_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                options={"temperature": 0.3},
            )
            raw = response.message.content.strip()
            raw = strip_thinking(raw)

            # Strip markdown code fences if model adds them
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.strip()

            insight = json.loads(raw)
            insight["n_posts"] = len(posts)
            insight["top_words"] = topic_words
            insight["status"] = "pending"
            return insight

        except json.JSONDecodeError as e:
            logger.warning(f"Topic {topic_id} attempt {attempt + 1}: JSON parse error: {e}")
            if attempt == retries:
                return None
        except Exception as e:
            logger.error(f"Topic {topic_id} attempt {attempt + 1}: {e}")
            if attempt < retries:
                time.sleep(2)
            else:
                return None

    return None


def get_representative_posts(
    df: pl.DataFrame, topic_id: int, n: int = MAX_POSTS_PER_TOPIC
) -> list[dict]:
    topic_df = df.filter(pl.col("topic_id") == topic_id)
    if topic_df.is_empty():
        return []

    topic_df = topic_df.with_columns(
        pl.col("score").fill_null(0).cast(pl.Float64).alias("eng"),
        pl.col("full_text").str.len_chars().cast(pl.Float64).alias("text_len"),
    )
    max_eng = topic_df["eng"].max() or 1.0
    max_len = topic_df["text_len"].max() or 1.0

    topic_df = topic_df.with_columns(
        (0.6 * pl.col("eng") / max_eng + 0.4 * pl.col("text_len") / max_len).alias("sel_score")
    ).sort("sel_score", descending=True)

    # Ensure source diversity
    sources = topic_df["source"].unique().to_list()
    per_source = max(2, n // len(sources))
    selected: dict[str, dict] = {}

    for src in sources:
        for row in topic_df.filter(pl.col("source") == src).head(per_source).to_dicts():
            selected[row["id"]] = row

    rows = sorted(selected.values(), key=lambda r: r.get("sel_score", 0), reverse=True)
    return rows[:n]


def run() -> list[dict]:
    client = ollama.Client(host=OLLAMA_HOST)

    # Verify model is available
    try:
        models = [m.model for m in client.list().models]
        if OLLAMA_MODEL not in models:
            available = ", ".join(models)
            logger.error(f"Model '{OLLAMA_MODEL}' not found. Available: {available}")
            return []
        logger.info(f"Using local model: {OLLAMA_MODEL}")
    except Exception as e:
        logger.error(f"Cannot connect to Ollama at {OLLAMA_HOST}: {e}")
        return []

    # Load data (prefer most-enriched available)
    for filename in ["with_sentiment.ndjson", "with_topics.ndjson", "cleaned.ndjson"]:
        path = PROCESSED_DIR / filename
        if path.exists():
            logger.info(f"Loading {path.name}")
            df = pl.read_ndjson(path, infer_schema_length=None)
            break
    else:
        raise FileNotFoundError("Run preprocess.py first.")

    if "topic_id" not in df.columns:
        logger.error("No topic_id column — run topic_model.py first.")
        return []

    # Load topic word map
    topic_words_map: dict[int, str] = {}
    summary_path = PROCESSED_DIR / "topic_summary.csv"
    if summary_path.exists():
        ts = pl.read_csv(summary_path)
        topic_words_map = dict(
            zip(ts["topic_id"].to_list(), ts["top_words"].to_list(), strict=False)
        )

    # Topics to process
    topic_counts = (
        df.filter(pl.col("topic_id") != -1)
        .group_by("topic_id")
        .len()
        .filter(pl.col("len") >= MIN_TOPIC_SIZE)
        .sort("len", descending=True)
        .head(MAX_TOPICS)
    )
    topics = topic_counts["topic_id"].to_list()
    logger.info(f"Synthesizing {len(topics)} topics via {OLLAMA_MODEL}...")

    output_path = INSIGHTS_DIR / "insights.json"
    insights = []
    for i, topic_id in enumerate(topics, 1):
        topic_words = topic_words_map.get(topic_id, "")
        posts = get_representative_posts(df, topic_id)
        if not posts:
            continue

        logger.info(f"[{i}/{len(topics)}] Topic {topic_id}: {topic_words[:60]}")
        insight = synthesize_topic(client, topic_id, topic_words, posts)
        if insight:
            insights.append(insight)
            # Save after each card so progress survives interruption
            with open(output_path, "w") as f:
                json.dump(insights, f, indent=2, default=str)
            logger.success(f"  → saved card {len(insights)} ({insight.get('category', '?')}): {insight.get('headline', '')[:60]}")
        else:
            logger.warning(f"  → failed to generate card for topic {topic_id}")

    logger.success(f"Saved {len(insights)} insight cards → {output_path}")

    print(f"\nGenerated {len(insights)} insight cards")
    print("Categories:", dict(Counter(i.get("category") for i in insights)))
    flagged = sum(1 for i in insights if i.get("needs_human_review"))
    print(f"Flagged for human review: {flagged}")
    return insights


if __name__ == "__main__":
    run()
