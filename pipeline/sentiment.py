"""
Sentiment analysis using HuggingFace transformers (ProsusAI/finbert).

Usage:
    uv run python pipeline/sentiment.py
"""

import polars as pl
from tqdm import tqdm
from transformers import pipeline as hf_pipeline

from pipeline.config import PROCESSED_DIR, SENTIMENT_MODEL, logger

BATCH_SIZE = 32
MAX_LENGTH = 512


def load_data() -> pl.DataFrame:
    for filename in ["with_topics.ndjson", "cleaned.ndjson"]:
        path = PROCESSED_DIR / filename
        if path.exists():
            logger.info(f"Loading {path.name}")
            return pl.read_ndjson(path)
    raise FileNotFoundError("Run preprocess.py first.")


def normalize_label(label: str) -> str:
    label = label.lower()
    if label in ("positive", "pos", "label_2"):
        return "positive"
    if label in ("negative", "neg", "label_0"):
        return "negative"
    return "neutral"


def run_sentiment(texts: list[str]) -> list[dict]:
    logger.info(f"Loading sentiment model: {SENTIMENT_MODEL}")
    pipe = hf_pipeline(
        "sentiment-analysis",
        model=SENTIMENT_MODEL,
        tokenizer=SENTIMENT_MODEL,
        truncation=True,
        max_length=MAX_LENGTH,
        batch_size=BATCH_SIZE,
        device=-1,
    )

    results = []
    logger.info(f"Running sentiment on {len(texts):,} texts...")
    for i in tqdm(range(0, len(texts), BATCH_SIZE), desc="Sentiment batches"):
        batch = texts[i : i + BATCH_SIZE]
        try:
            results.extend(pipe(batch))
        except Exception as e:
            logger.warning(f"Batch {i} failed: {e} — filling with neutral")
            results.extend([{"label": "neutral", "score": 0.5}] * len(batch))
    return results


def run() -> pl.DataFrame:
    df = load_data()
    texts = df["full_text"].to_list()
    raw = run_sentiment(texts)

    df = df.with_columns(
        pl.Series("sentiment_label_raw", [r["label"] for r in raw]),
        pl.Series("sentiment_score", [float(r["score"]) for r in raw]),
    ).with_columns(
        pl.col("sentiment_label_raw")
        .map_elements(normalize_label, return_dtype=pl.String)
        .alias("sentiment_label")
    )

    # Topic-level sentiment summary
    if "topic_id" in df.columns:
        topic_sent = (
            df.filter(pl.col("topic_id") != -1)
            .group_by("topic_id")
            .agg(
                pl.len().alias("n_docs"),
                (pl.col("sentiment_label") == "positive").mean().alias("pct_positive"),
                (pl.col("sentiment_label") == "negative").mean().alias("pct_negative"),
                (pl.col("sentiment_label") == "neutral").mean().alias("pct_neutral"),
                pl.col("sentiment_score").mean().alias("avg_score"),
            )
            .sort("pct_negative", descending=True)
        )
        topic_sent.write_csv(PROCESSED_DIR / "topic_sentiment.csv")
        logger.info("Saved → data/processed/topic_sentiment.csv")

    df.write_ndjson(PROCESSED_DIR / "with_sentiment.ndjson")
    logger.success(f"Saved {len(df):,} records → data/processed/with_sentiment.ndjson")

    print("\nSentiment distribution:")
    print(df.group_by("sentiment_label").len().sort("len", descending=True))
    return df


if __name__ == "__main__":
    run()
