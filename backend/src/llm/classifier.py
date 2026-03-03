"""
LLMClassifier — orchestrates LLM-based feedback classification.

Provider priority:
  1. Ollama local (llama3 by default) — primary for local runs, no quota
  2. Gemini 2.0 Flash (free tier: 15 RPM, 1,500 req/day) — fallback

Never raises — always returns a result dict. Failed classifications are
marked with classification_status='failed' so they can be retried later.
"""

import json
import logging
import os
import time

from src.llm.gemini_client import GeminiClient, GeminiQuotaError, GeminiRateLimitError
from src.llm.ollama_client import OllamaClient
from src.llm.prompt_builder import PromptBuilder

logger = logging.getLogger(__name__)

VALID_CATEGORIES = {
    "feature_request",
    "bug_report",
    "complaint",
    "praise",
    "general_discussion",
}


class LLMClassifier:
    """
    Classifies raw feedback items using an LLM.

    Uses Ollama first (no quota, works offline); falls back to Gemini
    if Ollama is unavailable or returns an unparseable response.
    A 4-second delay is inserted between Gemini calls to respect the
    free-tier 15 RPM limit.
    """

    def __init__(self) -> None:
        self.ollama = OllamaClient()
        self.gemini = GeminiClient()
        self.prompt_builder = PromptBuilder()
        self.delay = float(os.environ.get("CLASSIFIER_DELAY_SECONDS", "5"))

    def classify(self, raw_item: dict, product: dict) -> dict:
        """
        Classify a single raw feedback item.

        Args:
            raw_item: A dict with at least a 'content' key (from raw_feedback table).
            product:  A product dict from ProductRepository.

        Returns:
            A dict with keys:
                category, sentiment, summary, topics, confidence,
                llm_provider, classification_status
            On failure, classification_status='failed' and llm_provider='unknown'.
            This method never raises.
        """
        prompt = self.prompt_builder.build_classification_prompt(
            raw_item["content"], product
        )

        # --- Primary: Ollama (local, no quota) ---
        try:
            raw_json = self.ollama.generate(prompt)
            result = self._parse_result(raw_json)
            if result:
                return {
                    **result,
                    "llm_provider": "ollama",
                    "classification_status": "success",
                }
        except Exception as exc:  # noqa: BLE001
            logger.warning("Ollama unavailable: %s. Falling back to Gemini.", exc)

        # --- Fallback: Gemini (cloud, free tier) ---
        if os.environ.get("OLLAMA_ONLY") == "1":
            logger.warning("Ollama failed and OLLAMA_ONLY=1 — skipping Gemini fallback.")
            return {"classification_status": "failed", "llm_provider": "ollama"}

        try:
            raw_json = self.gemini.generate(prompt)
            result = self._parse_result(raw_json)
            if result:
                time.sleep(self.delay)  # respect free-tier RPM
                return {
                    **result,
                    "llm_provider": "gemini",
                    "classification_status": "success",
                }
        except (GeminiQuotaError, GeminiRateLimitError) as exc:
            logger.error("Gemini quota/rate limit: %s. Marking item as failed.", exc)
        except Exception as exc:  # noqa: BLE001
            logger.error("Gemini error: %s. Marking item as failed.", exc)

        return {"classification_status": "failed", "llm_provider": "unknown"}

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _parse_result(self, raw: str) -> dict | None:
        """
        Parse and validate the JSON response from an LLM.

        Strips markdown fences if present. When the model outputs multiple
        JSON objects (common with smaller local models), takes the first
        well-formed object that contains a valid category. Returns None if
        no valid classification can be extracted.

        Args:
            raw: The raw string response from the LLM.

        Returns:
            A validated dict with classification fields, or None on failure.
        """
        try:
            text = raw.strip()
            # Strip markdown fences in case the model ignores the instruction
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0]

            # Try a straight parse first (well-behaved models)
            try:
                candidates = [json.loads(text)]
            except json.JSONDecodeError:
                # Some models emit multiple JSON objects; use a streaming decoder
                # to extract all of them and pick the first valid one.
                candidates = []
                decoder = json.JSONDecoder()
                pos = 0
                while pos < len(text):
                    try:
                        obj, end = decoder.raw_decode(text, pos)
                        candidates.append(obj)
                        pos = end
                    except json.JSONDecodeError:
                        pos += 1

            for data in candidates:
                if not isinstance(data, dict):
                    continue
                if data.get("category") not in VALID_CATEGORIES:
                    continue
                return {
                    "category": data["category"],
                    "sentiment": float(data.get("sentiment", 0)),
                    "summary": str(data.get("summary", ""))[:120],
                    "topics": data.get("topics", [])[:5],
                    "confidence": float(data.get("confidence", 0)),
                }

            logger.warning(
                "No valid category found in LLM response. Raw (first 200): %r",
                raw[:200],
            )
            return None
        except (KeyError, ValueError) as exc:
            logger.warning(
                "Failed to parse LLM response: %s. Raw (first 200): %r",
                exc,
                raw[:200],
            )
            return None
