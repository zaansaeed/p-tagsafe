from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List
import google.generativeai as genai
import os, math

router = APIRouter(prefix="/ranking", tags=["ranking"])
MODEL_ID = "gemini-2.5-flash-lite"
EMB_MODEL_ID = "text-embedding-004"   

api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)
client = genai.GenerativeModel(
        MODEL_ID
)

class RankRequest(BaseModel):
    user_text: str = Field(..., description="User's product text / description")
    phrases: List[str] = Field(..., description="Candidate phrases to reorder")

def _cosine(a, b) -> float:
    dot = sum(x*y for x, y in zip(a, b))
    na = math.sqrt(sum(x*x for x in a)) + 1e-9
    nb = math.sqrt(sum(y*y for y in b)) + 1e-9
    return dot / (na * nb)

def _embed_one(text: str) -> List[float]:
    """
    Embed a single text using Gemini. Returns the embedding vector (list of floats).
    """
    # task_type is optional; you can set it to "retrieval_query" / "retrieval_document" depending on use.
    res = genai.embed_content(
        model=EMB_MODEL_ID,
        content=text,
        task_type="semantic_similarity",  # sensible default for ranking; omit if undesired
    )
    # The SDK returns {'embedding': {'values': [...]}} OR {'embedding': [...] } depending on version.
    emb = res.get("embedding", res)  # be tolerant
    return emb

def _embed(texts: List[str]) -> list[list[float]]:
    return [_embed_one(t) for t in texts]

@router.post("/rank", response_model=List[str])
def rank_phrases(req: RankRequest):
    phrases = [p.strip() for p in req.phrases if p and p.strip()]
    if not phrases:
        return []
    # lower case everything to dedupe
    seen, uniq = set(), []
    for p in phrases:
        k = p.lower()
        if k not in seen:
            seen.add(k)
            uniq.append(p)
    phrases = uniq
    # Embed user text + phrases in one shot
    embeds = _embed([req.user_text] + phrases)
    user_vec, phrase_vecs = embeds[0], embeds[1:]

    # Score & sort
    scored = [(phrases[i], _cosine(phrase_vecs[i], user_vec)) for i in range(len(phrases))]
    scored.sort(key=lambda t: (-t[1], len(t[0]), t[0]))  # tie-break: shorter, then alpha

    # Return just the reordered list of phrases
    return [phrase for phrase, _ in scored]