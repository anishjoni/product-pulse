"""
Centralized configuration: environment validation and logging setup.
Import this at the top of any pipeline module to get consistent logging and
fail-fast env checks.

Usage:
    from pipeline.config import logger, require_env

    # Validate a required env var (exits with clear message if missing):
    api_key = require_env("ANTHROPIC_API_KEY")

    # Optional env var with default:
    user_agent = optional_env("REDDIT_USER_AGENT", "WealthsimpleCommunityIntel/1.0")
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

# Load .env file if present (silently OK if missing — env vars may be set externally)
load_dotenv()

# ── Logging setup ─────────────────────────────────────────────────────────────
# Remove default loguru sink and add a nicely formatted one
logger.remove()
logger.add(
    sys.stderr,
    format=(
        "<green>{time:HH:mm:ss}</green> "
        "<dim>|</dim> <level>{level: <8}</level> "
        "<dim>|</dim> <cyan>{name}</cyan>:<cyan>{function}</cyan> "
        "<dim>—</dim> {message}"
    ),
    colorize=True,
    level="INFO",
)
# Also write full logs to a rotating file for debugging
logger.add(
    "logs/pipeline_{time:YYYY-MM-DD}.log",
    rotation="50 MB",
    retention="7 days",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} — {message}",
)

# Ensure logs directory exists
Path("logs").mkdir(exist_ok=True)


# ── Env helpers ───────────────────────────────────────────────────────────────
def require_env(key: str) -> str:
    """
    Get a required environment variable.
    Exits with a clear, actionable error message if missing.
    """
    value = os.getenv(key)
    if not value:
        logger.error(f"Required environment variable not set: {key}")
        logger.info("  → Copy .env.example to .env and fill in your credentials")
        logger.info(f"  → Or set it directly: export {key}=your_value")
        sys.exit(1)
    return value


def optional_env(key: str, default: str = "") -> str:
    """Get an optional environment variable with a default."""
    return os.getenv(key, default)


# ── Path constants ────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
MODELS_DIR = DATA_DIR / "models"
INSIGHTS_DIR = DATA_DIR / "insights"

for _dir in (RAW_DIR, PROCESSED_DIR, MODELS_DIR, INSIGHTS_DIR):
    _dir.mkdir(parents=True, exist_ok=True)


# ── Model config ──────────────────────────────────────────────────────────────
GEMINI_MODEL = "gemini-2.0-flash"  # free tier, fast, excellent quality
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
SENTIMENT_MODEL = "ProsusAI/finbert"

WEALTHSIMPLE_KEYWORDS = [
    "wealthsimple",
    "wealth simple",
    "ws trade",
    "wstrade",
    "ws crypto",
    "wealthsimple trade",
    "wealthsimple cash",
    "wealthsimple invest",
    "ws invest",
    "wealthsimple tax",
]
