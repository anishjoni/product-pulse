#!/usr/bin/env python3
"""Discover relevant feedback sources for a product and optionally add or create it.

Usage (from project root):
    bash execution/discover_sources.sh "Mintlify"                        # discover only
    bash execution/discover_sources.sh "Mintlify" --add --product-id 3  # add to existing
    bash execution/discover_sources.sh "Mintlify" --create               # create new product
    bash execution/discover_sources.sh "Wealthsimple" --country ca --create
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import textwrap
from dataclasses import asdict, dataclass

import httpx
from dotenv import load_dotenv

_HERE = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_HERE, "..", "backend", ".env"))

API_BASE = os.environ.get("PULSE_API_BASE", "http://localhost:8000")


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class DiscoveredSource:
    source_type: str   # reddit | youtube | google_play | apple_app_store
    source_ref: str    # raw identifier stored in the DB
    display: str       # human-readable label
    confidence: str    # "confirmed" | "suggested"


# ---------------------------------------------------------------------------
# Discovery: Google Play
# ---------------------------------------------------------------------------

def discover_google_play(query: str, country: str) -> list[DiscoveredSource]:
    try:
        from google_play_scraper import search as gplay_search
        results = gplay_search(query, n_hits=5, lang="en", country=country)
        out = []
        for r in results[:5]:
            app_id = r.get("appId")
            if not app_id:
                continue
            title = r.get("title", app_id)
            score = r.get("score")
            score_str = f" {score:.1f}★" if score else ""
            installs = r.get("installs", "")
            installs_str = f" · {installs}" if installs else ""
            out.append(DiscoveredSource(
                source_type="google_play",
                source_ref=f"{app_id}:{country}",
                display=f"{title}{score_str}{installs_str}  ({app_id})",
                confidence="confirmed",
            ))
            if len(out) == 3:
                break
        return out
    except Exception as e:
        print(f"  [!] Google Play search failed: {e}", file=sys.stderr)
        return []


# ---------------------------------------------------------------------------
# Discovery: Apple App Store
# ---------------------------------------------------------------------------

def discover_app_store(query: str, country: str) -> list[DiscoveredSource]:
    try:
        resp = httpx.get(
            "https://itunes.apple.com/search",
            params={"term": query, "entity": "software", "limit": 5, "country": country},
            timeout=10,
        )
        resp.raise_for_status()
        out = []
        for r in resp.json().get("results", [])[:3]:
            track_id = str(r["trackId"])
            title = r.get("trackName", track_id)
            rating = r.get("averageUserRatingForCurrentVersion") or r.get("averageUserRating")
            rating_str = f" {rating:.1f}★" if rating else ""
            out.append(DiscoveredSource(
                source_type="apple_app_store",
                source_ref=f"{track_id}:{country}",
                display=f"{title}{rating_str}  (id{track_id})",
                confidence="confirmed",
            ))
        return out
    except Exception as e:
        print(f"  [!] App Store search failed: {e}", file=sys.stderr)
        return []


# ---------------------------------------------------------------------------
# Discovery: Reddit + YouTube + keywords via Gemini (single call)
# ---------------------------------------------------------------------------

def discover_via_gemini(product_name: str) -> tuple[list[DiscoveredSource], list[str]]:
    """Returns (community_sources, suggested_keywords)."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("  [!] GEMINI_API_KEY not set — skipping Reddit/YouTube/keyword suggestions.", file=sys.stderr)
        return [], []
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            generation_config={"temperature": 0.2, "response_mime_type": "application/json"},
        )
        prompt = textwrap.dedent(f"""\
            You are helping set up feedback monitoring for a software product called "{product_name}".

            Return a JSON object with exactly these keys:

            "subreddits": array of up to 5 subreddit names (no "r/" prefix) where users discuss
              this product. Put the product's own subreddit first if one exists, then closely
              related communities. Only include subreddits that very likely exist and are active.

            "youtube_searches": array of up to 3 YouTube search query strings that surface
              real user reviews, tutorials, or comparisons for this product.
              Good examples: ["Mintlify review", "Mintlify tutorial", "Mintlify vs alternatives"]

            "keywords": array of 5–10 short search keywords or phrases useful for filtering
              community posts about this product. Include the product name, common feature names,
              and close synonyms. These will be used to filter scraped posts by relevance.
              Good examples: ["mintlify", "docs ai", "documentation tool", "api docs"]

            Return ONLY the JSON object. No markdown, no explanation.
        """)
        response = model.generate_content(prompt)
        data = json.loads(response.text)

        sources: list[DiscoveredSource] = []
        for sub in data.get("subreddits", []):
            sub = sub.strip().lower().lstrip("r/").lstrip("/")
            if sub:
                sources.append(DiscoveredSource(
                    source_type="reddit",
                    source_ref=sub,
                    display=f"r/{sub}",
                    confidence="suggested",
                ))
        for term in data.get("youtube_searches", []):
            term = term.strip()
            if term:
                sources.append(DiscoveredSource(
                    source_type="youtube",
                    source_ref=term,
                    display=f'"{term}"',
                    confidence="suggested",
                ))

        keywords = [k.strip() for k in data.get("keywords", []) if k.strip()]
        return sources, keywords

    except Exception as e:
        print(f"  [!] Gemini lookup failed: {e}", file=sys.stderr)
        return [], []


# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------

LABELS = {
    "google_play":    "Google Play",
    "apple_app_store": "App Store  ",
    "reddit":         "Reddit     ",
    "youtube":        "YouTube    ",
}


def print_results(by_type: dict[str, list[DiscoveredSource]]) -> None:
    for source_type, sources in by_type.items():
        if not sources:
            continue
        print(f"\n  {LABELS.get(source_type, source_type)}")
        for s in sources:
            tag = "confirmed" if s.confidence == "confirmed" else "suggested"
            print(f"    [{tag}]  {s.display}")


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------

def get_all_products() -> list[dict]:
    resp = httpx.get(f"{API_BASE}/products", timeout=10)
    resp.raise_for_status()
    return resp.json()


def get_product(product_id: int) -> dict:
    for p in get_all_products():
        if p["id"] == product_id:
            return p
    raise ValueError(f"Product ID {product_id} not found.")


def add_sources_to_product(product_id: int, new_sources: list[DiscoveredSource]) -> dict:
    product = get_product(product_id)
    existing_keys = {(s["source_type"], s["source_ref"]) for s in product.get("sources", [])}
    merged = list(product.get("sources", []))
    added = 0
    for s in new_sources:
        if (s.source_type, s.source_ref) not in existing_keys:
            merged.append({"source_type": s.source_type, "source_ref": s.source_ref})
            existing_keys.add((s.source_type, s.source_ref))
            added += 1
    resp = httpx.put(
        f"{API_BASE}/products/{product_id}",
        json={"keywords": product.get("keywords", []), "sources": merged},
        timeout=10,
    )
    resp.raise_for_status()
    return {"added": added, "total": len(merged)}


def create_product(
    name: str,
    slug: str,
    description: str,
    keywords: list[str],
    sources: list[DiscoveredSource],
) -> dict:
    resp = httpx.post(
        f"{API_BASE}/products",
        json={
            "name": name,
            "slug": slug,
            "description": description or None,
            "keywords": keywords,
            "sources": [{"source_type": s.source_type, "source_ref": s.source_ref} for s in sources],
        },
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[\s_]+", "-", text)


def prompt(label: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    val = input(f"  {label}{suffix}: ").strip()
    return val if val else default


def prompt_list(label: str, default: list[str]) -> list[str]:
    default_str = ", ".join(default)
    suffix = f" [{default_str}]" if default_str else ""
    raw = input(f"  {label}{suffix}: ").strip()
    if not raw:
        return default
    return [k.strip() for k in raw.split(",") if k.strip()]


# ---------------------------------------------------------------------------
# Interactive source picker
# ---------------------------------------------------------------------------

def prompt_selection(all_sources: list[DiscoveredSource]) -> list[DiscoveredSource]:
    print()
    print("  #   Type               Source")
    print("  " + "-" * 58)
    for i, s in enumerate(all_sources, 1):
        tag = "✓" if s.confidence == "confirmed" else "~"
        type_label = LABELS.get(s.source_type, s.source_type).strip()
        print(f"  {i:>2}. [{tag}] {type_label:<18}  {s.display}")
    print()
    print("  Enter numbers to add (comma-separated), 'all', or Enter to cancel:")
    raw = input("  > ").strip()
    if not raw:
        return []
    if raw.lower() == "all":
        return all_sources
    try:
        indices = [int(x.strip()) - 1 for x in raw.split(",")]
        return [all_sources[i] for i in indices if 0 <= i < len(all_sources)]
    except (ValueError, IndexError):
        print("  Invalid selection.")
        return []


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Discover feedback sources for a product.")
    parser.add_argument("product_name", help="Product or app name to search for")
    parser.add_argument("--country", default="us", metavar="CC",
                        help="Country code for app stores (default: us)")
    parser.add_argument("--product-id", type=int, metavar="ID",
                        help="Existing product ID to add sources to (used with --add)")
    parser.add_argument("--add", action="store_true",
                        help="Add discovered sources to an existing product")
    parser.add_argument("--create", action="store_true",
                        help="Create a new product with the discovered sources")
    parser.add_argument("--json", dest="as_json", action="store_true",
                        help="Print discovered sources as JSON and exit")
    args = parser.parse_args()

    country = args.country.lower()
    print(f'\nDiscovering sources for "{args.product_name}" [{country.upper()}] ...\n')

    play_sources        = discover_google_play(args.product_name, country)
    store_sources       = discover_app_store(args.product_name, country)
    community, keywords = discover_via_gemini(args.product_name)
    reddit_sources      = [s for s in community if s.source_type == "reddit"]
    youtube_sources     = [s for s in community if s.source_type == "youtube"]
    all_sources         = play_sources + store_sources + reddit_sources + youtube_sources

    if args.as_json:
        print(json.dumps([asdict(s) for s in all_sources], indent=2))
        return

    print_results({
        "google_play":     play_sources,
        "apple_app_store": store_sources,
        "reddit":          reddit_sources,
        "youtube":         youtube_sources,
    })

    if keywords:
        print(f"\n  Suggested keywords: {', '.join(keywords)}")

    if not all_sources:
        print("\n  No sources found.")
        return

    # ── --create: new product flow ──────────────────────────────────────────
    if args.create:
        print("\n  Select sources to include:")
        selected = prompt_selection(all_sources)
        if not selected:
            print("\n  Nothing selected — product not created.")
            return

        print()
        name        = prompt("Product name", args.product_name)
        slug        = prompt("Slug", slugify(name))
        description = prompt("Description")
        kws         = prompt_list("Keywords (comma-separated)", keywords)

        print(f'\n  Creating "{name}" with {len(selected)} source(s)...')
        try:
            product = create_product(name, slug, description, kws, selected)
            print(f"  Created product (id: {product['id']})")
            print(f"  Open http://localhost:3005/products/{product['slug']}/dashboard")
        except Exception as e:
            print(f"\n  Failed to create product: {e}")
            sys.exit(1)
        return

    # ── --add: existing product flow ────────────────────────────────────────
    if args.add:
        product_id = args.product_id
        if not product_id:
            try:
                products = get_all_products()
                print("\n  Available products:")
                for p in products:
                    print(f"    {p['id']:>3}.  {p['name']}  ({p['slug']})")
                product_id = int(input("\n  Product ID: ").strip())
            except Exception as e:
                print(f"\n  Could not reach API: {e}")
                sys.exit(1)

        print("\n  Select sources to add:")
        selected = prompt_selection(all_sources)
        if not selected:
            print("\n  Nothing added.")
            return

        try:
            result = add_sources_to_product(product_id, selected)
            print(f"\n  Added {result['added']} new source(s). "
                  f"Product now has {result['total']} source(s) total.")
        except Exception as e:
            print(f"\n  Failed to add sources: {e}")
            sys.exit(1)
        return

    print("\n  Run with --add [--product-id ID] to add to an existing product.")
    print("  Run with --create to create a new product.")


if __name__ == "__main__":
    main()
