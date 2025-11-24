from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from PIL import Image
import io

from updated_description_gen import (
    generating_phrases,
    label_and_filter_phrases,
    compose_safe_listing_description_from_phrases,
)

from tag_generator_api import generate_tags_from_llm

router = APIRouter(prefix="/compose", tags=["compose"])


class ComposeResponse(BaseModel):
    safe_phrases: list[str]
    all_labeled: list[dict]
    tags: list[str]
    safe_listing_description: str   


@router.post("/all", response_model=ComposeResponse)
async def compose_all(
    title: str = Form(...),
    nice_class: int = Form(...),
    product_text: str = Form(default=""),
    image_file: UploadFile = File(None),
):
    title = (title or "").strip()
    if not title:
        raise HTTPException(status_code=400, detail="title is required")

    # Generate description phrases and label them
    try:
        generated_text = generating_phrases(title)
        labeled, safe = label_and_filter_phrases(generated_text)
        safe_phrases = [r["phrase"] for r in safe]
        safe_listing_description = compose_safe_listing_description_from_phrases(
        title=title,
        safe_phrases=safe_phrases,
    )


    except Exception as e:
        raise HTTPException(status_code=502, detail=f"description generation failed: {e}")

    # Generate tags only if image provided
    tags: list[str] = []
    if image_file is not None:
        content_type = image_file.content_type or "image/png"
        if not content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Invalid image file")
        img_bytes = await image_file.read()
        if not img_bytes:
            raise HTTPException(status_code=400, detail="Empty image file")
        try:
            img = Image.open(io.BytesIO(img_bytes))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid image: {e}")

        try:
            tags = generate_tags_from_llm(nice_class=nice_class, product_text=product_text, image=img)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"tag generation failed: {e}")

    return {
        "safe_phrases": safe_phrases,
        "all_labeled": labeled,
        "tags": tags,
        "safe_listing_description": safe_listing_description,
    }
