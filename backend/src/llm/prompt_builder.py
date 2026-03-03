"""
PromptBuilder — constructs LLM prompts for feedback classification.

Keeps prompt logic in one place so it is easy to iterate and test in isolation.
"""


class PromptBuilder:
    """Builds classification prompts for the LLM classifier."""

    def build_classification_prompt(self, content: str, product: dict) -> str:
        """
        Build a classification prompt for the given content and product context.

        Args:
            content: The raw post/comment text to classify.
            product: A product dict from ProductRepository (includes name,
                     description, and keywords list).

        Returns:
            A fully-formed prompt string ready to pass to an LLM.
        """
        keywords_csv = ", ".join(product.get("keywords", [])[:10])
        return f"""Classify the community post below about {product['name']}.

Context: {product.get('description', '')}
Keywords: {keywords_csv}

Post:
---
{content[:2000]}
---

Rules:
- Reply with ONLY a JSON object — nothing else.
- Do NOT write any text before or after the JSON.
- Do NOT use markdown, code fences, or any explanation.

Required JSON format (fill in the values):
{{"category":"<feature_request|bug_report|complaint|praise|general_discussion>","sentiment":<float -1.0 to 1.0>,"summary":"<one sentence max 120 chars third person>","topics":["<keyword>"],"confidence":<float 0.0 to 1.0>}}"""
