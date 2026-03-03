"""
eval_classifiers.py — Compare BERT-class vs LLM classifications.

Usage (run from backend/ directory via the shell script):
    python -m src.experiments.eval_classifiers <product_id> <n_samples>

Metrics produced:
  1. Category agreement %  (overall + per-category breakdown)
  2. Confusion matrix       (rows = LLM label, cols = BERT label)
  3. Sentiment Pearson r + MAE
  4. Confidence distributions (mean ± std for BERT vs LLM)
  5. BERT inference speed  (total wall-clock + ms/item)
  6. Top disagreements     (high LLM-confidence but category mismatch)

Output:
  - Pretty-printed report to stdout
  - Full results saved to backend/data/eval_bert_vs_llm.json
"""

from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Resolve DB path relative to this script's location (backend/src/experiments/)
# ---------------------------------------------------------------------------
_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent  # backend/
_DATA_DIR = _BACKEND_DIR / "data"
_DEFAULT_DB = _DATA_DIR / "pulse.db"

VALID_CATEGORIES = [
    "feature_request",
    "bug_report",
    "complaint",
    "praise",
    "general_discussion",
]


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_items(db_path: Path, product_id: int, n: int) -> list[dict]:
    """
    Pull N randomly-sampled, successfully-classified items from the DB
    for the given product.
    """
    import sqlite3

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(
            """
            SELECT rf.id,
                   rf.content,
                   rf.source,
                   cf.category       AS llm_category,
                   cf.sentiment      AS llm_sentiment,
                   cf.confidence     AS llm_confidence,
                   cf.llm_provider
            FROM   raw_feedback rf
            JOIN   classified_feedback cf ON cf.raw_feedback_id = rf.id
            WHERE  cf.classification_status = 'success'
              AND  rf.product_id = ?
            ORDER  BY RANDOM()
            LIMIT  ?
            """,
            (product_id, n),
        )
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Metrics helpers
# ---------------------------------------------------------------------------

def _pearson_r(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 2:
        return float("nan")
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    denom = math.sqrt(
        sum((x - mean_x) ** 2 for x in xs) * sum((y - mean_y) ** 2 for y in ys)
    )
    return num / denom if denom else float("nan")


def _mae(xs: list[float], ys: list[float]) -> float:
    return sum(abs(x - y) for x, y in zip(xs, ys)) / len(xs)


def _mean_std(values: list[float]) -> tuple[float, float]:
    if not values:
        return float("nan"), float("nan")
    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    return mean, math.sqrt(variance)


def build_confusion_matrix(
    llm_labels: list[str], bert_labels: list[str]
) -> dict[str, dict[str, int]]:
    """Return a nested dict confusion[llm][bert] = count."""
    matrix: dict[str, dict[str, int]] = {
        cat: {c: 0 for c in VALID_CATEGORIES} for cat in VALID_CATEGORIES
    }
    for llm, bert in zip(llm_labels, bert_labels):
        if llm in matrix and bert in matrix[llm]:
            matrix[llm][bert] += 1
    return matrix


# ---------------------------------------------------------------------------
# Report formatting
# ---------------------------------------------------------------------------

def _fmt_confusion(matrix: dict[str, dict[str, int]]) -> str:
    short = {
        "feature_request": "feat_req",
        "bug_report": "bug_rep",
        "complaint": "complnt",
        "praise": "praise ",
        "general_discussion": "gen_dis",
    }
    header = f"{'LLM \\ BERT':<14}" + "".join(f"{short[c]:>9}" for c in VALID_CATEGORIES)
    rows = [header, "-" * len(header)]
    for llm_cat in VALID_CATEGORIES:
        row = f"{short[llm_cat]:<14}"
        for bert_cat in VALID_CATEGORIES:
            row += f"{matrix[llm_cat][bert_cat]:>9}"
        rows.append(row)
    return "\n".join(rows)


def print_report(
    items: list[dict],
    bert_results: list[dict],
    bert_ms_total: float,
) -> dict:
    """Print a human-readable report and return the full results dict."""
    n = len(items)

    llm_cats = [it["llm_category"] for it in items]
    bert_cats = [r["category"] for r in bert_results]

    llm_sents = [float(it["llm_sentiment"]) for it in items]
    bert_sents = [float(r["sentiment"]) for r in bert_results]

    llm_confs = [float(it["llm_confidence"]) for it in items]
    bert_confs = [float(r["confidence"]) for r in bert_results]

    # --- Agreement ---
    agree = [l == b for l, b in zip(llm_cats, bert_cats)]
    overall_pct = 100.0 * sum(agree) / n

    per_cat: dict[str, dict] = {}
    for cat in VALID_CATEGORIES:
        indices = [i for i, l in enumerate(llm_cats) if l == cat]
        if not indices:
            per_cat[cat] = {"llm_count": 0, "agree_pct": None}
        else:
            cat_agree = sum(agree[i] for i in indices)
            per_cat[cat] = {
                "llm_count": len(indices),
                "agree_pct": round(100.0 * cat_agree / len(indices), 1),
            }

    # --- Sentiment ---
    pearson = _pearson_r(llm_sents, bert_sents)
    mae = _mae(llm_sents, bert_sents)

    # --- Confidence ---
    llm_mean, llm_std = _mean_std(llm_confs)
    bert_mean, bert_std = _mean_std(bert_confs)

    # --- Speed ---
    ms_per_item = bert_ms_total / n if n else 0.0

    # --- Confusion matrix ---
    matrix = build_confusion_matrix(llm_cats, bert_cats)

    # --- Top disagreements ---
    disagreements = []
    for i, (it, br) in enumerate(zip(items, bert_results)):
        if it["llm_category"] != br["category"]:
            disagreements.append(
                {
                    "id": it["id"],
                    "llm_category": it["llm_category"],
                    "bert_category": br["category"],
                    "llm_confidence": round(float(it["llm_confidence"]), 3),
                    "snippet": it["content"][:80].replace("\n", " "),
                }
            )
    disagreements.sort(key=lambda d: d["llm_confidence"], reverse=True)

    # --- Print ---
    sep = "=" * 64
    print(sep)
    print("  BERT vs LLM Classifier Evaluation Report")
    print(sep)
    print(f"\n  Samples evaluated : {n}")
    print(f"  BERT total time   : {bert_ms_total:.0f} ms  ({ms_per_item:.1f} ms/item)")

    print(f"\n{'─' * 64}")
    print("  1. Category Agreement")
    print(f"{'─' * 64}")
    print(f"  Overall agreement : {overall_pct:.1f}%")
    print(f"\n  Per-category breakdown (LLM as reference):")
    for cat, info in per_cat.items():
        if info["llm_count"] == 0:
            print(f"    {cat:<22}  n=0")
        else:
            print(
                f"    {cat:<22}  n={info['llm_count']:<4}  agree={info['agree_pct']}%"
            )

    print(f"\n{'─' * 64}")
    print("  2. Confusion Matrix (rows = LLM, cols = BERT)")
    print(f"{'─' * 64}")
    print(_fmt_confusion(matrix))

    print(f"\n{'─' * 64}")
    print("  3. Sentiment Correlation")
    print(f"{'─' * 64}")
    print(f"  Pearson r : {pearson:.4f}")
    print(f"  MAE       : {mae:.4f}")

    print(f"\n{'─' * 64}")
    print("  4. Confidence Distributions")
    print(f"{'─' * 64}")
    print(f"  LLM  : mean={llm_mean:.3f}  std={llm_std:.3f}")
    print(f"  BERT : mean={bert_mean:.3f}  std={bert_std:.3f}")

    print(f"\n{'─' * 64}")
    print(f"  5. Top Disagreements (LLM high-confidence, label mismatch)")
    print(f"{'─' * 64}")
    for d in disagreements[:10]:
        print(
            f"  [id={d['id']}] llm={d['llm_category']}  bert={d['bert_category']}"
            f"  conf={d['llm_confidence']}"
        )
        print(f"    \"{d['snippet']}\"")

    print(f"\n{sep}\n")

    return {
        "n_samples": n,
        "bert_ms_total": round(bert_ms_total, 1),
        "bert_ms_per_item": round(ms_per_item, 1),
        "category_agreement_pct": round(overall_pct, 2),
        "per_category": per_cat,
        "confusion_matrix": matrix,
        "sentiment_pearson_r": round(pearson, 4) if not math.isnan(pearson) else None,
        "sentiment_mae": round(mae, 4),
        "llm_confidence_mean": round(llm_mean, 4),
        "llm_confidence_std": round(llm_std, 4),
        "bert_confidence_mean": round(bert_mean, 4),
        "bert_confidence_std": round(bert_std, 4),
        "top_disagreements": disagreements[:20],
    }


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> None:
    args = sys.argv[1:]
    product_id = int(args[0]) if len(args) > 0 else 1
    n_samples = int(args[1]) if len(args) > 1 else 100

    db_path = Path(
        __import__("os").environ.get(
            "DATABASE_URL", f"sqlite:///{_DEFAULT_DB}"
        ).replace("sqlite:///", "")
    )
    if not db_path.is_absolute():
        db_path = _BACKEND_DIR / db_path

    print(f"Loading {n_samples} items for product_id={product_id} from {db_path} …")
    items = load_items(db_path, product_id, n_samples)

    if not items:
        print(
            "ERROR: No classified items found for this product. "
            "Run a scout first, then retry.",
            file=sys.stderr,
        )
        sys.exit(1)

    actual_n = len(items)
    if actual_n < n_samples:
        print(f"Warning: only {actual_n} items available (requested {n_samples}).")

    print(f"Loading BERT models (first run downloads ~700 MB to ~/.cache/huggingface) …")
    from src.experiments.bert_classifier import BertClassifier  # noqa: PLC0415

    clf = BertClassifier()

    print(f"Running BERT inference on {actual_n} items …")
    t0 = time.perf_counter()
    bert_results = [clf.classify(it["content"]) for it in items]
    bert_ms = (time.perf_counter() - t0) * 1000.0

    results = print_report(items, bert_results, bert_ms)

    # --- Save JSON ---
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    out_path = _DATA_DIR / "eval_bert_vs_llm.json"
    out_path.write_text(json.dumps(results, indent=2))
    print(f"Full results saved to {out_path}")


if __name__ == "__main__":
    main()
