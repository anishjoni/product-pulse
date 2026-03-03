#!/usr/bin/env bash
# Search Google Play and Apple App Store for an app and return IDs.
# Use these IDs when adding google_play / apple_app_store sources to a product.
#
# Usage: bash execution/find_app_ids.sh "<search term>" [country]
#   country defaults to "us"  (use "ca" for Canadian apps like Wealthsimple)
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$REPO_ROOT/backend"
PY="$BACKEND/.venv/bin/python3"
QUERY="${1:-}"
COUNTRY="${2:-us}"

if [[ -z "$QUERY" ]]; then
  echo "Usage: bash execution/find_app_ids.sh \"<search term>\" [country]"
  exit 1
fi

"$PY" - "$QUERY" "$COUNTRY" <<'PYEOF'
import sys, re
sys.path.insert(0, ".")
import httpx

query, country = sys.argv[1], sys.argv[2]

# ── Google Play ───────────────────────────────────────────────────────────────
print(f"\n── Google Play results for '{query}' (country={country}) ──────────────")
try:
    resp = httpx.get(
        "https://play.google.com/store/search",
        params={"q": query, "c": "apps", "gl": country, "hl": "en"},
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
        timeout=10, follow_redirects=True,
    )
    ids = re.findall(r'/store/apps/details\?id=([\w.]+)', resp.text)
    seen, unique = set(), []
    for x in ids:
        if x not in seen:
            seen.add(x)
            unique.append(x)
    for app_id in unique[:5]:
        print(f"  {app_id}")
    if not unique:
        print("  (no results)")
except Exception as e:
    print(f"  ❌ Error: {e}")

# ── Apple App Store ───────────────────────────────────────────────────────────
print(f"\n── Apple App Store results for '{query}' (country={country}) ──────────")
try:
    resp = httpx.get(
        "https://itunes.apple.com/search",
        params={"term": query, "entity": "software", "limit": 5, "country": country},
        timeout=10,
    )
    resp.raise_for_status()
    results = resp.json().get("results", [])
    for r in results:
        print(f"  {r['trackId']}  —  {r['trackName']}")
    if not results:
        print("  (no results)")
except Exception as e:
    print(f"  ❌ Error: {e}")

print()
PYEOF
