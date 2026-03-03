"""
OllamaClient — thin wrapper around the local Ollama HTTP API.

Used as a fallback when Gemini quota is exhausted. Reads base URL and model
name from environment variables so they can be overridden without code changes.
"""

import logging
import os

import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class OllamaClient:
    """Calls a locally-running Ollama instance for text generation."""

    def __init__(self) -> None:
        self.base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = os.environ.get("OLLAMA_MODEL", "llama3")

    def generate(self, prompt: str) -> str:
        """
        POST to Ollama /api/generate and return the response string.

        Raises:
            httpx.HTTPStatusError: if Ollama returns a non-2xx status.
            httpx.ConnectError: if Ollama is not running / unreachable.
        """
        logger.info("Ollama ▶ %s (prompt: %d chars)", self.model, len(prompt))
        response = httpx.post(
            f"{self.base_url}/api/generate",
            json={"model": self.model, "prompt": prompt, "stream": False},
            timeout=120.0,
        )
        response.raise_for_status()
        text = response.json()["response"]
        logger.info("Ollama ◀ %d chars: %s", len(text), text[:120].replace("\n", " "))
        return text
