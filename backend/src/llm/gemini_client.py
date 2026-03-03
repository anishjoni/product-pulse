"""
GeminiClient — thin wrapper around the google-generativeai SDK.

Uses gemini-2.0-flash with temperature=0.1 and JSON response mode for
consistent, parseable output. Re-exports the quota/rate-limit exceptions
so callers can import them from this module.
"""

import os

import google.generativeai as genai
from dotenv import load_dotenv
from google.api_core.exceptions import ResourceExhausted, TooManyRequests

load_dotenv()

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Re-export for use in classifier.py
GeminiQuotaError = ResourceExhausted
GeminiRateLimitError = TooManyRequests


class GeminiClient:
    """Thin wrapper around the Gemini 2.0 Flash generative model."""

    def __init__(self) -> None:
        self.model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            generation_config={
                "temperature": 0.1,
                "response_mime_type": "application/json",
            },
        )

    def generate(self, prompt: str) -> str:
        """
        Send a prompt to Gemini and return the response text.

        Raises:
            GeminiQuotaError (ResourceExhausted): daily quota exceeded.
            GeminiRateLimitError (TooManyRequests): per-minute rate limit hit.
            Any other google.api_core exception on unexpected API errors.
        """
        response = self.model.generate_content(prompt)
        return response.text
