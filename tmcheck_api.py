# tmcheck_api.py
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, validator
import asyncio

from uspto_client import check_trademark_available, TMError

router = APIRouter(prefix="/tmcheck", tags=["tmcheck"])

# --- Request/Response models ---

class TMCheckRequest(BaseModel):
    phrases: List[str] = Field(..., description="Up to 50 candidate tags/phrases")
    nice_class: Optional[int] = Field(None, description="Nice class code, e.g., 25")
    min_safe: int = Field(8, ge=1, le=50, description="Minimum safe phrases to return")
    fallback_defaults: List[str] = Field(default_factory=list, description="Fallback safe-ish generics")

    @validator("phrases")
    def _limit_phrases(cls, v):
        # strip empties, de-dupe case-insensitively, cap at 50
        seen = set()
        out = []
        for p in (p.strip() for p in v if p and p.strip()):
            k = p.lower()
            if k not in seen:
                seen.add(k)
                out.append(p)
            if len(out) == 50:
                break
        if not out:
            raise ValueError("No valid phrases provided")
        return out

class PhraseDecision(BaseModel):
    phrase: str
    reasons: List[str]

class TMCheckResponse(BaseModel):
    ok: bool
    safe: List[str]
    blocked: List[PhraseDecision]
    meta: Dict[str, Any]

# --- Helpers ---

FAMOUS_MARKS = {
    "disney","pixar","marvel","harry potter","hogwarts",
    "nike","adidas","yeezy","puma",
    "apple","iphone","ipad","macbook",
    "coca-cola","coke","pepsi","sprite",
    "minecraft","fortnite","roblox","pokemon","nintendo",
    "barbie","lego","hello kitty","sanrio",
    "taylor swift","swiftie","swifties",
    "starbucks","mcdonalds","mcdonald's",
    "nba","nfl","mlb","nhl","fifa","olympics",
    "tesla","google","instagram","tiktok","youtube",
}

def coarse_blocklist_hit(phrase: str) -> Optional[str]:
    s = phrase.lower()
    for mark in FAMOUS_MARKS:
        if mark in s:
            return f"famous mark detected: {mark}"
    return None

def interpret_trademark_available_response(resp: Dict[str, Any]) -> Optional[str]:
    """
    Return None if looks safe; else a reason string.
    Accepts any shape from RapidAPI; errs on the side of caution.
    """
    if resp is None:
        return "USPTO empty response"

    # Transport-level error surfaced by wrapper
    if resp.get("error"):
        return resp["error"]

    status_code = resp.get("status_code")
    payload = resp.get("payload")

    # If API said something clearly bad at the HTTP layer:
    if isinstance(status_code, int) and status_code >= 400:
        return f"USPTO error {status_code}"

    # Try common dict shapes
    if isinstance(payload, dict):
        available = payload.get("available")
        status = (payload.get("status") or payload.get("result") or payload.get("message") or "").strip().lower()
        if available is True:
            return None
        if available is False:
            return "USPTO unavailable"
        if status in {"unavailable", "taken", "conflict"}:
            return "USPTO unavailable"
        # If dict but inconclusive, consider it safe (or flip to risky if you want stricter)
        return None

    # If it’s a list or string or unknown, be conservative but not fatal
    if isinstance(payload, list):
        # If any element looks like a conflict marker:
        text = " ".join(map(lambda x: str(x).lower(), payload[:5]))
        if any(k in text for k in ["unavailable", "taken", "conflict", "registered"]):
            return "USPTO unavailable"
        return None

    if isinstance(payload, str):
        low = payload.lower()
        if any(k in low for k in ["unavailable", "taken", "conflict", "registered"]):
            return "USPTO unavailable"
        return None

    # Unknown shape
    return None


# --- Core check ---

async def check_one_phrase(phrase: str, nice_class: Optional[int]) -> PhraseDecision | None:
    """
    Returns PhraseDecision if BLOCKED, or None if SAFE.
    """
    reasons: List[str] = []

    # 1) quick local blocklist
    hit = coarse_blocklist_hit(phrase)
    if hit:
        return PhraseDecision(phrase=phrase, reasons=[hit])

    # 2) remote availability
        # 2) remote availability
    try:
        resp = await check_trademark_available(phrase)
    except Exception as e:
        return PhraseDecision(phrase=phrase, reasons=[f"USPTO call exception: {e}"])

    reason = interpret_trademark_available_response(resp)
    if reason:
        reasons.append(reason)


    reason = interpret_trademark_available_response(resp)
    if reason:
        reasons.append(reason)

    # 3) OPTIONAL: if you later inspect classes in resp, you can do:
    # if nice_class is not None and class_hits_include(nice_class, resp):
    #     reasons.append(f"class {nice_class} conflict")

    return PhraseDecision(phrase=phrase, reasons=reasons) if reasons else None

# --- Route ---

@router.post("/v1/verify", response_model=TMCheckResponse)
async def verify_phrases(req: TMCheckRequest):
    phrases = req.phrases

    # Parallelize the remote checks
    tasks = [check_one_phrase(p, req.nice_class) for p in phrases]
    results = await asyncio.gather(*tasks)

    blocked_map = {r.phrase: r for r in results if r is not None}
    safe = [p for p in phrases if p not in blocked_map]

    # Ensure minimum safe by topping up from fallbacks
    if len(safe) < req.min_safe and req.fallback_defaults:
        # remove any fallback that is already blocked or duped
        existing = set(p.lower() for p in phrases)
        blocked_lower = set(k.lower() for k in blocked_map.keys())
        for fb in req.fallback_defaults:
            s = fb.strip()
            if not s:
                continue
            k = s.lower()
            if k in existing or k in blocked_lower or k in (x.lower() for x in safe):
                continue
            safe.append(s)
            if len(safe) >= req.min_safe:
                break

    blocked = list(blocked_map.values())

    return TMCheckResponse(
        ok=True,
        safe=safe,
        blocked=blocked,
        meta={
            "checked": len(phrases),
            "safe_count": len(safe),
            "min_safe_required": req.min_safe,
            "nice_class": req.nice_class,
            "api": "uspto-trademark.p.rapidapi.com",
        },
    )
