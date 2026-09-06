"""Simple visitor-purpose classifier. Uses keywords unless an AI API is configured."""

import os
import re

CATEGORIES = (
    "INTERVIEW",
    "BUSINESS MEETING",
    "DELIVERY",
    "ACADEMIC",
    "MAINTENANCE",
    "OTHER",
)

KEYWORD_MAP = {
    "INTERVIEW": (
        "interview",
        "recruitment",
        "hiring",
        "job",
        "hr round",
        "campus placement",
    ),
    "BUSINESS MEETING": (
        "meeting",
        "project manager",
        "client",
        "discussion with",
        "business",
        "vendor",
    ),
    "DELIVERY": (
        "deliver",
        "delivery",
        "package",
        "courier",
        "parcel",
        "drop off",
    ),
    "ACADEMIC": (
        "college",
        "project",
        "academic",
        "seminar",
        "research",
        "student",
        "viva",
        "thesis",
    ),
    "MAINTENANCE": (
        "maintenance",
        "repair",
        "technician",
        "ac service",
        "electrician",
        "plumber",
    ),
}


def classify_purpose(purpose_text):
    """Return a category label. Never raises; always returns a string."""
    text = (purpose_text or "").strip()
    if not text:
        return "OTHER"

    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if api_key:
        result = _classify_with_api(text, api_key)
        if result:
            return result
    return _classify_with_keywords(text)


def _classify_with_keywords(text):
    lowered = text.lower()
    scores = {}
    for category, keywords in KEYWORD_MAP.items():
        scores[category] = sum(1 for word in keywords if word in lowered)
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return "OTHER"
    return best


def _classify_with_api(text, api_key):
    """Optional OpenAI call. Returns None on any failure so keywords can be used."""
    try:
        import json
        import urllib.request

        payload = json.dumps(
            {
                "model": "gpt-4o-mini",
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Classify a visitor purpose into exactly one of: "
                            + ", ".join(CATEGORIES)
                            + ". Reply with the category only."
                        ),
                    },
                    {"role": "user", "content": text},
                ],
                "max_tokens": 20,
                "temperature": 0,
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=8) as response:
            body = json.loads(response.read().decode("utf-8"))
        label = body["choices"][0]["message"]["content"].strip().upper()
        label = re.sub(r"[^A-Z ]", "", label)
        for category in CATEGORIES:
            if category in label:
                return category
    except Exception:
        return None
    return None
