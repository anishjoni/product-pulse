"""
Topic modeling with BERTopic.
Discovers latent topics from community feedback.

Usage:
    uv run python pipeline/topic_model.py
"""

import numpy as np
import polars as pl
from bertopic import BERTopic
from hdbscan import HDBSCAN
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import CountVectorizer
from umap import UMAP

from pipeline.config import EMBEDDING_MODEL, MODELS_DIR, PROCESSED_DIR, logger

MIN_TOPIC_SIZE = 10
N_GRAM_RANGE = (1, 2)


def _cast_null_cols(df: pl.DataFrame) -> pl.DataFrame:
    """Cast any Null-typed columns to String so ndjson writes don't fail."""
    null_cols = [c for c, t in zip(df.columns, df.dtypes, strict=False) if t == pl.Null]
    if null_cols:
        df = df.with_columns([pl.lit(None, dtype=pl.String).alias(c) for c in null_cols])
    return df


def load_processed() -> pl.DataFrame:
    path = PROCESSED_DIR / "cleaned.ndjson"
    if not path.exists():
        raise FileNotFoundError(f"Run preprocess.py first. Missing: {path}")
    return pl.read_ndjson(path, infer_schema_length=None)


def build_topic_model(docs: list[str]) -> tuple[BERTopic, list[int], np.ndarray]:
    logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
    embedding_model = SentenceTransformer(EMBEDDING_MODEL)

    umap_model = UMAP(
        n_neighbors=15, n_components=5, min_dist=0.0, metric="cosine", random_state=42
    )
    hdbscan_model = HDBSCAN(
        min_cluster_size=MIN_TOPIC_SIZE,
        metric="euclidean",
        cluster_selection_method="eom",
        prediction_data=True,
    )
    vectorizer_model = CountVectorizer(ngram_range=N_GRAM_RANGE, stop_words="english", min_df=2)

    model = BERTopic(
        embedding_model=embedding_model,
        umap_model=umap_model,
        hdbscan_model=hdbscan_model,
        vectorizer_model=vectorizer_model,
        top_n_words=10,
        verbose=True,
    )

    logger.info(f"Fitting BERTopic on {len(docs):,} documents...")
    topics, probs = model.fit_transform(docs)
    n_topics = len(model.get_topic_info()) - 1  # exclude outlier topic -1
    logger.success(f"Discovered {n_topics} topics")
    return model, topics, probs


def assign_intent(topic_words: str) -> str:
    """Heuristic intent tagging — Claude refines this in synthesize.py."""
    t = topic_words.lower()
    friction = [
        "error",
        "bug",
        "broken",
        "crash",
        "slow",
        "issue",
        "fail",
        "fee",
        "wait",
        "support",
    ]
    roadmap = ["want", "wish", "need", "request", "add", "should", "missing", "improve", "option"]
    win = ["love", "great", "amazing", "best", "awesome", "easy", "recommend", "perfect", "like"]

    scores = {
        "friction": sum(1 for s in friction if s in t),
        "roadmap": sum(1 for s in roadmap if s in t),
        "win": sum(1 for s in win if s in t),
    }
    top = max(scores, key=scores.get)
    return top if scores[top] > 0 else "other"


def run() -> tuple[pl.DataFrame, BERTopic]:
    df = load_processed()
    docs = df["full_text"].to_list()

    model, topics, probs = build_topic_model(docs)

    # Attach topic assignments
    topic_probs = [float(p.max()) if hasattr(p, "__len__") else float(p) for p in probs]
    df = df.with_columns(
        pl.Series("topic_id", topics),
        pl.Series("topic_prob", topic_probs),
    )
    _cast_null_cols(df).write_ndjson(PROCESSED_DIR / "with_topics.ndjson")
    logger.info("Saved → data/processed/with_topics.ndjson")

    # Topic summary
    info = model.get_topic_info()
    topic_rows = []
    for _, row in info.iterrows():
        tid = int(row["Topic"])
        if tid == -1:
            continue
        top_words = ", ".join(w for w, _ in model.get_topic(tid)[:8])
        topic_rows.append(
            {
                "topic_id": tid,
                "count": int(row["Count"]),
                "top_words": top_words,
                "intent": assign_intent(top_words),
            }
        )

    summary = pl.DataFrame(topic_rows).sort("count", descending=True)
    summary.write_csv(PROCESSED_DIR / "topic_summary.csv")
    logger.info("Saved → data/processed/topic_summary.csv")

    # Save model
    model.save(
        str(MODELS_DIR / "bertopic_model"),
        serialization="safetensors",
        save_ctfidf=True,
    )
    logger.success("BERTopic model saved")

    print("\nTop topics:")
    print(summary.head(15))
    return df, model


if __name__ == "__main__":
    run()
