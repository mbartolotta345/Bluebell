"""Plant care lookup via the Google Custom Search JSON API.

This does NOT use an LLM - it runs a web search and extracts a
watering frequency and sunlight phrase from the returned snippets with
simple regex/keyword heuristics. That makes it free to run (Google's
Custom Search API has a 100 queries/day free tier) but less reliable
and precise than an LLM-generated answer: it can miss values that are
phrased unusually, or grab a plausible-looking number from an
unrelated part of a snippet. Always treat the result as a starting
point the user should double-check, not a verified fact.
"""
import os
import re

import requests

SEARCH_URL = "https://www.googleapis.com/customsearch/v1"

# Longest/most specific phrases first, so "bright indirect light" wins
# over a later, looser match like "bright light".
SUNLIGHT_PHRASES = [
    "bright, indirect light",
    "bright indirect light",
    "bright indirect sunlight",
    "medium indirect light",
    "low indirect light",
    "direct sunlight",
    "indirect sunlight",
    "indirect light",
    "full sun",
    "partial shade",
    "partial sun",
    "full shade",
    "low light",
    "medium light",
    "bright light",
    "filtered light",
    "morning sun",
]

FREQUENCY_PATTERNS = [
    (re.compile(r"every\s+(\d+)\s*(?:to|-)\s*(\d+)\s*days", re.I), lambda m: round((int(m.group(1)) + int(m.group(2))) / 2)),
    (re.compile(r"every\s+(\d+)\s+days", re.I), lambda m: int(m.group(1))),
    (re.compile(r"once\s+every\s+(\d+)\s+weeks?", re.I), lambda m: int(m.group(1)) * 7),
    (re.compile(r"once\s+a\s+week|once\s+per\s+week|weekly", re.I), lambda m: 7),
    (re.compile(r"twice\s+a\s+week|twice\s+per\s+week", re.I), lambda m: 3),
    (re.compile(r"once\s+a\s+month|monthly", re.I), lambda m: 30),
]

DEFAULT_FREQUENCY_DAYS = 7
DEFAULT_SUNLIGHT = "Bright, indirect light"


class AiLookupError(Exception):
    pass


def _get_credentials():
    api_key = os.environ.get("GOOGLE_API_KEY")
    cse_id = os.environ.get("GOOGLE_CSE_ID")
    if not api_key or not cse_id:
        raise AiLookupError(
            "GOOGLE_API_KEY and GOOGLE_CSE_ID must be configured on the server."
        )
    return api_key, cse_id


def _search(species):
    api_key, cse_id = _get_credentials()
    query = f"{species} houseplant watering frequency sunlight needs care"

    try:
        response = requests.get(
            SEARCH_URL,
            params={"key": api_key, "cx": cse_id, "q": query, "num": 5},
            timeout=10,
        )
    except requests.RequestException as exc:
        raise AiLookupError(f"Search request failed: {exc}") from exc

    if response.status_code != 200:
        raise AiLookupError(
            f"Search request failed with status {response.status_code}: {response.text[:200]}"
        )

    items = response.json().get("items") or []
    if not items:
        raise AiLookupError(f"No search results found for '{species}'.")
    return items


def _extract_frequency(text):
    for pattern, resolver in FREQUENCY_PATTERNS:
        match = pattern.search(text)
        if match:
            return resolver(match)
    return None


def _extract_sunlight(text):
    lowered = text.lower()
    for phrase in SUNLIGHT_PHRASES:
        if phrase in lowered:
            return phrase[0].upper() + phrase[1:]
    return None


def get_care_suggestion(species):
    """Searches for the species' care needs and extracts a suggestion.

    Returns a dict: suggested_frequency_days, suggested_sunlight,
    explanation, sources (list of URLs). Values are best-effort
    extractions from search snippets, not an authoritative answer.
    """
    items = _search(species)

    snippets = [item.get("snippet", "") for item in items]
    sources = [item.get("link") for item in items if item.get("link")]
    combined_text = " ".join(snippets)

    frequency = _extract_frequency(combined_text)
    sunlight = _extract_sunlight(combined_text)

    used_defaults = []
    if frequency is None:
        frequency = DEFAULT_FREQUENCY_DAYS
        used_defaults.append("watering frequency")
    if sunlight is None:
        sunlight = DEFAULT_SUNLIGHT
        used_defaults.append("sunlight needs")

    best_snippet = next((s for s in snippets if s), "")
    explanation = f"From top search results for \"{species}\": {best_snippet}".strip()
    if used_defaults:
        explanation += (
            f" (Could not find a clear {' or '.join(used_defaults)} in search "
            f"results, so a common default was used - please verify.)"
        )

    return {
        "suggested_frequency_days": frequency,
        "suggested_sunlight": sunlight,
        "explanation": explanation,
        "sources": sources,
    }
