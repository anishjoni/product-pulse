#!/usr/bin/env bash
# Diagnose the Product Pulse stack:
#   - Ollama reachability + loaded models
#   - DB row counts and recent scout runs
#   - Live test classification via Ollama
#
# Usage: bash execution/diagnose.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$REPO_ROOT/backend"
VENV="$BACKEND/.venv"
PY="$VENV/bin/python3"

if [[ ! -x "$PY" ]]; then
  echo "ERROR: venv not found. Run run_api.sh first to ensure the venv exists."
  exit 1
fi

cd "$BACKEND"
export DATABASE_URL="${DATABASE_URL:-sqlite:///./data/pulse.db}"
export OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://localhost:11434}"
# OLLAMA_MODEL is intentionally NOT defaulted here — let Python load it from .env

echo "========================================"
echo "  Product Pulse Diagnostics"
echo "========================================"

"$PY" - <<'PYEOF'
import sys, json, os
sys.path.insert(0, ".")

# ── DB stats ─────────────────────────────────────────────────────────────────
print("\n── Database stats ───────────────────────────────")
from src.db.database import get_db
with get_db() as conn:
    rf  = conn.execute("SELECT COUNT(*) FROM raw_feedback").fetchone()[0]
    cf_ok  = conn.execute("SELECT COUNT(*) FROM classified_feedback WHERE classification_status='success'").fetchone()[0]
    cf_fail= conn.execute("SELECT COUNT(*) FROM classified_feedback WHERE classification_status='failed'").fetchone()[0]
    tr  = conn.execute("SELECT COUNT(*) FROM trends").fetchone()[0]
    runs = conn.execute(
        "SELECT id, triggered_by, status, items_fetched, items_classified, started_at FROM scout_runs ORDER BY id DESC LIMIT 5"
    ).fetchall()

print(f"  raw_feedback       : {rf} rows")
print(f"  classified success : {cf_ok} rows")
print(f"  classified failed  : {cf_fail} rows")
print(f"  trends             : {tr} rows")

print("\n── Recent scout runs (newest first) ─────────────")
if runs:
    for r in runs:
        print(f"  #{r['id']:3d} | {r['status']:10s} | fetched={r['items_fetched']:4d} classified={r['items_classified']:4d} | {r['triggered_by']:9s} | {r['started_at']}")
else:
    print("  No scout runs found.")

# ── Source breakdown ──────────────────────────────────────────────────────────
print("\n── Raw feedback by source ───────────────────────")
with get_db() as conn:
    rows = conn.execute(
        "SELECT source, COUNT(*) as n FROM raw_feedback GROUP BY source ORDER BY n DESC"
    ).fetchall()
    for r in rows:
        print(f"  {r['source']:12s}: {r['n']} posts")

# ── Ollama ────────────────────────────────────────────────────────────────────
print("\n── Ollama ───────────────────────────────────────")
import httpx
base = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
model = os.environ.get("OLLAMA_MODEL", "llama3")
try:
    tags = httpx.get(f"{base}/api/tags", timeout=5).json()
    models = [m["name"] for m in tags.get("models", [])]
    print(f"  Status  : ✅ running at {base}")
    print(f"  Models  : {', '.join(models) if models else '(none loaded)'}")
    target_loaded = any(model in m for m in models)
    print(f"  {model:10s}: {'✅ loaded' if target_loaded else '⚠️  NOT found — run: ollama pull ' + model}")
except Exception as e:
    print(f"  Status  : ❌ unreachable ({e})")
    print(f"  Fix     : make sure ollama is running  →  ollama serve")
    sys.exit(0)

# ── Live classification test ───────────────────────────────────────────────────
print("\n── Live Ollama classification test ──────────────")
from src.llm.ollama_client import OllamaClient
from src.llm.classifier import LLMClassifier
from src.llm.prompt_builder import PromptBuilder

sample_product = {
    "name": "Wealthsimple Trade",
    "description": "Commission-free stock and ETF trading app",
    "keywords": ["wealthsimple", "trade", "options", "tfsa"],
}
sample_raw_item = {
    "content": "The app keeps crashing whenever I try to open the options chain on my iPhone. Super frustrating, been happening for 3 days.",
}

# Show raw Ollama response first so we can see what the model is actually saying
try:
    prompt = PromptBuilder().build_classification_prompt(sample_raw_item["content"], sample_product)
    raw = OllamaClient().generate(prompt)
    print(f"  Raw response  : {raw[:300].replace(chr(10), ' ')}")
except Exception as e:
    print(f"  Ollama call   : ❌ failed — {e}")
    raw = None

# Parse using the real LLMClassifier (handles preamble, fences, multi-object responses)
if raw is not None:
    parsed = LLMClassifier()._parse_result(raw)
    if parsed:
        print(f"  Category      : {parsed.get('category')}")
        print(f"  Sentiment     : {parsed.get('sentiment')}")
        print(f"  Summary       : {parsed.get('summary')}")
        print(f"  Confidence    : {parsed.get('confidence')}")
        print(f"  Topics        : {parsed.get('topics')}")
        print("  Result        : ✅ classification working")
    else:
        print("  Result        : ❌ parse failed — no valid category found in response")

print("\n========================================")
PYEOF
