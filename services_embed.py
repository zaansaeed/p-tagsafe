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
    """
    Batch embed all texts in a single API call for massive performance gain.
    Falls back to sequential if batch fails.
    """
    if not texts:
        return []
    
    if len(texts) == 1:
        return [embed_text(texts[0])]
    
    try:
        # Batch embed all texts at once
        result = genai.embed_content(
            model=EMB_MODEL_ID,
            content=texts,
            task_type="semantic_similarity"
        )
        
        # Handle batch response format - Google API returns dict with 'embedding' key for batches
        if isinstance(result, dict):
            # Check for batch response with 'embedding' containing list of embeddings
            if "embedding" in result:
                emb = result["embedding"]
                # If it's a list of vectors, return them
                if isinstance(emb, list) and len(emb) > 0:
                    if isinstance(emb[0], list):
                        # Already a list of embeddings
                        return emb
                    elif isinstance(emb[0], (int, float)):
                        # Single embedding vector
                        return [emb]
                # Otherwise normalize as single embedding
                return [_normalize_embedding(result)]
            # Check for 'embeddings' plural (some API versions)
            elif "embeddings" in result:
                embeddings = result["embeddings"]
                if isinstance(embeddings, list):
                    return [_normalize_embedding(e) for e in embeddings]
        elif isinstance(result, list):
            # List of embeddings
            return [_normalize_embedding(r) for r in result]
        
        # Fallback to sequential
        print(f"Unexpected batch embedding format: {type(result)}, falling back to sequential")
        return [embed_text(t) for t in texts]
    except Exception as e:
        print(f"Batch embedding failed ({e}), falling back to sequential")
        return [embed_text(t) for t in texts]