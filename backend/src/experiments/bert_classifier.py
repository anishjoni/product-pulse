"""
BertClassifier — local zero-shot category + sentiment classification.

Models used:
  Category:  cross-encoder/nli-deberta-v3-small  (~180MB, zero-shot NLI)
  Sentiment: cardiffnlp/twitter-roberta-base-sentiment-latest (~500MB)

Both pipelines are loaded once at __init__ time and reused across calls.
Content is truncated to 512 chars before inference to avoid tokeniser
overflow on very long posts.

This module has NO side-effects on the live application — it is imported
only from the eval_classifiers experiment script.
"""

from __future__ import annotations

LABEL_MAP: dict[str, str] = {
    "feature request or product improvement": "feature_request",
    "bug report or technical problem": "bug_report",
    "complaint or user frustration": "complaint",
    "praise or positive feedback": "praise",
    "general discussion or question": "general_discussion",
}

_CANDIDATE_LABELS = list(LABEL_MAP.keys())

_MAX_CHARS = 512


class BertClassifier:
    """
    Wraps two HuggingFace pipelines for category + sentiment inference.

    Lazy-loads models on first instantiation so import does not trigger
    a download.
    """

    def __init__(self) -> None:
        from transformers import pipeline  # type: ignore[import-untyped]

        self._zero_shot = pipeline(
            "zero-shot-classification",
            model="cross-encoder/nli-deberta-v3-small",
            device=-1,  # CPU
        )
        self._sentiment = pipeline(
            "sentiment-analysis",
            model="cardiffnlp/twitter-roberta-base-sentiment-latest",
            return_all_scores=True,
            device=-1,  # CPU
        )

    def classify(self, content: str) -> dict:
        """
        Classify a single piece of feedback text.

        Args:
            content: Raw feedback string (will be truncated to 512 chars).

        Returns:
            {
                "category":   str,    # one of the 5 valid category enums
                "sentiment":  float,  # positive_score - negative_score, in [-1, 1]
                "confidence": float,  # zero-shot top-label score, in [0, 1]
            }
        """
        text = content[:_MAX_CHARS]

        # --- Category via zero-shot NLI ---
        zs_result = self._zero_shot(text, candidate_labels=_CANDIDATE_LABELS)
        top_label: str = zs_result["labels"][0]
        confidence: float = float(zs_result["scores"][0])
        category = LABEL_MAP[top_label]

        # --- Sentiment via RoBERTa ---
        sent_result = self._sentiment(text)  # list of {label, score} dicts
        scores: dict[str, float] = {d["label"]: d["score"] for d in sent_result}

        # Label keys from this model: "positive", "neutral", "negative"
        positive = scores.get("positive", scores.get("LABEL_2", 0.0))
        negative = scores.get("negative", scores.get("LABEL_0", 0.0))
        sentiment = float(positive - negative)

        return {
            "category": category,
            "sentiment": sentiment,
            "confidence": confidence,
        }
