"""
Preprocessing pipeline: cleaning, deduplication, language filtering, and merging
of Reddit and App Store raw data into a single analysis-ready DataFrame.

Usage:
    uv run python pipeline/preprocess.py
"""

import re

import polars as pl

from pipeline.config import (
    PROCESSED_DIR,
    RAW_DIR,
    WEALTHSIMPLE_KEYWORDS,
    logger,
)

MIN_TEXT_LEN = 30
MAX_TEXT_LEN = 5000

# Subreddits where all posts are WS-relevant (no keyword filter needed)
WS_SUBREDDITS = {"wealthsimple"}
APP_SOURCES = {"google_play", "app_store"}


def _clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)  # markdown links
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)  # headers
    return re.sub(r"\s+", " ", text).strip()


def _is_english(text: str) -> bool:
    try:
        from langdetect import detect

        return detect(text) == "en"
    except Exception:
        return True


def _is_ws_relevant(text: str) -> bool:
    t = text.lower()
    return any(kw in t for kw in WEALTHSIMPLE_KEYWORDS)


def load_raw() -> pl.DataFrame:
    frames = []
    for path in sorted(RAW_DIR.glob("*.ndjson")):
        logger.info(f"Loading {path.name}")
        frames.append(pl.read_ndjson(path))

    if not frames:
        raise FileNotFoundError(f"No .ndjson files found in {RAW_DIR}. Run collect_*.py first.")

    df = pl.concat(frames, how="diagonal")
    logger.info(f"Loaded {len(df):,} total records from {len(frames)} files")
    return df


def build_full_text(df: pl.DataFrame) -> pl.DataFrame:
    """Combine title + text into a single full_text column using polars expressions."""
    return df.with_columns(
        pl.when(pl.col("title").is_not_null() & (pl.col("title") != ""))
        .then(pl.col("title") + " " + pl.col("text").fill_null(""))
        .otherwise(pl.col("text").fill_null(""))
        .alias("full_text")
    )


def run() -> pl.DataFrame:
    df = load_raw()

    # 1. Build full_text
    df = build_full_text(df)

    # 2. Clean text (map_elements is the polars equivalent of apply for Python logic)
    logger.info("Cleaning text...")
    df = df.with_columns(
        pl.col("full_text").map_elements(_clean_text, return_dtype=pl.String).alias("full_text")
    )

    # 3. Length filters
    df = df.filter(
        (pl.col("full_text").str.len_chars() >= MIN_TEXT_LEN)
        & (pl.col("full_text").str.len_chars() <= MAX_TEXT_LEN)
    )
    logger.info(f"After length filter: {len(df):,}")

    # 4. Deduplicate on full_text
    df = df.unique(subset=["full_text"])
    logger.info(f"After dedup: {len(df):,}")

    # 5. Language detection (only for Reddit — app reviews already filtered to 'en')
    logger.info("Running language detection on Reddit posts...")
    reddit_df = df.filter(pl.col("source") == "reddit")
    other_df = df.filter(pl.col("source") != "reddit")

    is_english = reddit_df["full_text"].map_elements(_is_english, return_dtype=pl.Boolean)
    reddit_df = reddit_df.with_columns(is_english.alias("is_english"))
    other_df = other_df.with_columns(pl.lit(True).alias("is_english"))

    df = pl.concat([reddit_df.filter(pl.col("is_english")), other_df], how="diagonal")
    logger.info(f"After English filter: {len(df):,}")

    # 6. Wealthsimple relevance filter
    ws_subreddit_mask = pl.col("subreddit").str.to_lowercase().is_in(list(WS_SUBREDDITS))
    app_source_mask = pl.col("source").is_in(list(APP_SOURCES))
    always_relevant = ws_subreddit_mask | app_source_mask

    needs_filter_df = df.filter(~always_relevant)
    always_relevant_df = df.filter(always_relevant)

    ws_mask = needs_filter_df["full_text"].map_elements(_is_ws_relevant, return_dtype=pl.Boolean)
    filtered_df = needs_filter_df.filter(ws_mask)

    df = pl.concat([always_relevant_df, filtered_df], how="diagonal")
    logger.info(f"After WS relevance filter: {len(df):,}")

    # 7. Parse dates + add year_month
    df = df.with_columns(
        pl.col("created_utc").cast(pl.Utf8).str.to_datetime(strict=False).alias("created_utc")
    ).with_columns(
        pl.col("created_utc").dt.strftime("%Y-%m").alias("year_month")
    )

    # 8. Select final columns
    keep = ["id", "source", "subreddit", "type", "full_text", "title",
            "url", "score", "num_comments", "rating", "created_utc", "year_month", "author"]
    for col in keep:
        if col not in df.columns:
            df = df.with_columns(pl.lit(None).alias(col))
    df = df.select(keep)

    # 9. Save
    output_path = PROCESSED_DIR / "cleaned.ndjson"
    df.write_ndjson(output_path)
    logger.success(f"Saved {len(df):,} records → {output_path}")

    print(f"\nProcessed dataset: {len(df):,} records")
    print(df.group_by("source").len().sort("len", descending=True))

    return df


if __name__ == "__main__":
    run()
