# uspto_client.py
import os
import urllib.parse
from typing import Optional, Dict, Any
import httpx

RAPIDAPI_HOST = "uspto-trademark.p.rapidapi.com"
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY") or os.getenv("X_RAPIDAPI_KEY")  # allow either name

if not RAPIDAPI_KEY:
    raise RuntimeError("Missing RAPIDAPI_KEY (RapidAPI USPTO)")

HEADERS = {
    "x-rapidapi-host": RAPIDAPI_HOST,
    "x-rapidapi-key": RAPIDAPI_KEY,
}

BASE = f"https://{RAPIDAPI_HOST}/v1"

class TMError(Exception):
    pass

async def check_trademark_available(term: str) -> Dict[str, Any]:
    """
    GET /v1/trademarkAvailable/{term}
    Be tolerant of non-JSON and non-200 responses; never raise here.
    """
    safe_term = urllib.parse.quote(term)
    url = f"{BASE}/trademarkAvailable/{safe_term}"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(url, headers=HEADERS)
    except Exception as e:
        # Network/transport error
        return {"status_code": None, "payload": None, "error": f"http error: {e}"}

    try:
        payload = r.json()
    except Exception:
        payload = {"raw": r.text}

    return {
        "status_code": r.status_code,
        "payload": payload,   # could be dict/list/str-ish
        "error": None
    }


async def fulltext_search(term: str) -> Dict[str, Any]:
    """
    OPTIONAL enrichment: search broader text to inspect classes/owners if available.
    If your plan allows GET form, prefer that; otherwise, post form-encoded as docs show.
    Example fallback: GET /v1/trademarkSearch/amazon/{searchType} is too vague here,
    so we keep a generic "full text" helper if needed later.
    """
    # If the product offers a GET full-text search, you can wire it here.
    # For now, return empty to keep things robust.
    return {}
