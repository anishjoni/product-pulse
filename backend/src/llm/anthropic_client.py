"""
AnthropicClient — thin wrapper around the Anthropic SDK.

Used as a secondary fallback when Gemini quota is exhausted.
Model: claude-haiku-4-5-20251001 (fast, cost-effective, matches project memory spec).
"""

import os

import anthropic
from dotenv import load_dotenv

load_dotenv()


class AnthropicClient:
    """Calls Claude Haiku via the Anthropic SDK for text generation."""

    def __init__(self) -> None:
        self._client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        self.model = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")

    def generate(self, prompt: str) -> str:
        """
        Send a prompt to Claude Haiku and return the response text.

        Args:
            prompt: The full prompt text to send.

        Returns:
            The model's response as a plain string.

        Raises:
            anthropic.APIError: on API errors (rate limit, auth, etc.).
        """
        message = self._client.messages.create(
            model=self.model,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text
