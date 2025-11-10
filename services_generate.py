from typing import Any
from config import get_model

def generate_multimodal(model_id: str, prompt: str, image_bytes: bytes, content_type: str, generation_config: dict | None = None) -> Any:
    """
    Simple helper that builds a multi-part request (prompt + image bytes)
    and returns the raw SDK response. Callers should parse as-needed.
    """
    model = get_model(model_id)
    parts = [prompt, {"mime_type": content_type, "data": image_bytes}]
    cfg = generation_config or {}
    return model.generate_content(parts, generation_config=cfg)