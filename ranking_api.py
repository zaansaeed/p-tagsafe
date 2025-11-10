from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List
import math
from config import MODEL_ID, EMB_MODEL_ID, get_model
from services_embed import embed_texts

router = APIRouter(prefix="/ranking", tags=["ranking"])

client = get_model(MODEL_ID)

class RankRequest(BaseModel):
    user_text: str = Field(..., description="User's product text / description")
    phrases: List[str] = Field(..., description="Candidate phrases to reorder")

def _cosine(a, b) -> float:
    dot = sum(x*y for x, y in zip(a, b))
    na = math.sqrt(sum(x*x for x in a)) + 1e-9
    nb = math.sqrt(sum(y*y for y in b)) + 1e-9
    return dot / (na * nb)

def _embed(texts: List[str]) -> list[list[float]]:
    # delegate to service that normalizes SDK responses
    return embed_texts(texts)

@router.post("/rank", response_model=List[str])
def rank_phrases(req: RankRequest):
    phrases = [p.strip() for p in req.phrases if p and p.strip()]
    if not phrases:
        return []
    # dedupe preserving first occurrence
    seen, uniq = set(), []
    for p in phrases:
        k = p.lower()
        if k not in seen:
            seen.add(k)
            uniq.append(p)
    phrases = uniq
    # Embed user text + phrases
    try:
        embeds = _embed([req.user_text] + phrases)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Embedding failed: {e}")
    user_vec, phrase_vecs = embeds[0], embeds[1:]
    # Score & sort
    scored = [(phrases[i], _cosine(phrase_vecs[i], user_vec)) for i in range(len(phrases))]
    scored.sort(key=lambda t: (-t[1], len(t[0]), t[0]))
    return [phrase for phrase, _ in scored]