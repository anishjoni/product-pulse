"""
source_discovery.py — Find relevant feedback sources for a product/app name.

Used by:
  - GET /products/discover-sources  (API endpoint)
  - execution/discover_sources.py   (CLI script)
"""

from __future__ import annotations

import json
import os
import textwrap
from dataclasses import dataclass

import httpx


@dataclass
class DiscoveredSource:
    source_type: str   # reddit | youtube | google_play | apple_app_store
    source_ref: str    # raw identifier stored in the DB
    display: str       # human-readable label shown in the UI
    confidence: str    # "confirmed" (real API) | "suggested" (LLM)


@dataclass
class DiscoveryResult:
    sources: list[DiscoveredSource]
    keywords: list[str]


# ---------------------------------------------------------------------------
# Google Play
# ---------------------------------------------------------------------------

def _search_google_play(query: str, country: str) -> list[DiscoveredSource]:
    try:
        from google_play_scraper import search as gplay_search
        results = gplay_search(query, n_hits=5, lang="en", country=country)
        out: list[DiscoveredSource] = []
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
                display=f"{title}{score_str}{installs_str}",
                confidence="confirmed",
            ))
            if len(out) == 3:
                break
        return out
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Apple App Store (iTunes public search API)
# ---------------------------------------------------------------------------

def _search_app_store(query: str, country: str) -> list[DiscoveredSource]:
    try:
        resp = httpx.get(
            "https://itunes.apple.com/search",
            params={"term": query, "entity": "software", "limit": 5, "country": country},
            timeout=10,
        )
        resp.raise_for_status()
        out: list[DiscoveredSource] = []
        for r in resp.json().get("results", [])[:3]:
            track_id = str(r["trackId"])
            title = r.get("trackName", track_id)
            rating = r.get("averageUserRatingForCurrentVersion") or r.get("averageUserRating")
            rating_str = f" {rating:.1f}★" if rating else ""
            out.append(DiscoveredSource(
                source_type="apple_app_store",
                source_ref=f"{track_id}:{country}",
                display=f"{title}{rating_str}",
                confidence="confirmed",
            ))
        return out
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Reddit + YouTube + Keywords via Gemini
# ---------------------------------------------------------------------------

def _search_via_gemini(product_name: str) -> tuple[list[DiscoveredSource], list[str]]:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
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
              this product. Put the product's own subreddit first if one likely exists, then
              closely related communities. Only include subreddits that very likely exist.

            "youtube_searches": array of up to 3 YouTube search query strings that surface
              real user reviews, tutorials, or comparisons for this product.

            "keywords": array of 5–10 short search keywords or phrases for filtering community
              posts about this product. Include the product name, common feature names, synonyms.

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
                    display=term,
                    confidence="suggested",
                ))

        keywords = [k.strip() for k in data.get("keywords", []) if k.strip()]
        return sources, keywords

    except Exception:
        return [], []


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def discover(product_name: str, country: str = "us") -> DiscoveryResult:
    """Run all discovery sources and return combined results."""
    play_sources  = _search_google_play(product_name, country)
    store_sources = _search_app_store(product_name, country)
    community, keywords = _search_via_gemini(product_name)

    all_sources = play_sources + store_sources + community
    return DiscoveryResult(sources=all_sources, keywords=keywords)
