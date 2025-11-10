from typing import List
import google.generativeai as genai
from config import EMB_MODEL_ID

def _normalize_embedding(res) -> List[float]:
    """
    Normalize possible SDK shapes into a plain list[float].
    Handles:
      - {'embedding': [floats...]}
      - {'embedding': {'values': [floats...]}}
      - {'data': [{'embedding': [floats...]}]}
      - raw list [floats...]
    """
    if isinstance(res, dict):
        if "embedding" in res:
            emb = res["embedding"]
            if isinstance(emb, dict) and "values" in emb:
                return emb["values"]
            if isinstance(emb, list):
                return emb
        if "data" in res and isinstance(res["data"], list) and res["data"]:
            first = res["data"][0]
            if isinstance(first, dict) and "embedding" in first:
                e = first["embedding"]
                if isinstance(e, dict) and "values" in e:
                    return e["values"]
                if isinstance(e, list):
                    return e
    if isinstance(res, list):
        return res
    raise ValueError("Unexpected embedding response shape")

def embed_text(text: str) -> List[float]:
    res = genai.embed_content(model=EMB_MODEL_ID, content=text, task_type="semantic_similarity")
    return _normalize_embedding(res)

def embed_texts(texts: List[str]) -> List[List[float]]:
    return [embed_text(t) for t in texts]