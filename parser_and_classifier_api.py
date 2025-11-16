# parser_api.py
import os, json
from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException
from config import MODEL_ID, get_model

# Base model used for OCR + classification
model = get_model(MODEL_ID)

SYSTEM_INSTRUCTIONS = (
    "You are a vision assistant. Extract readable text from the image and "
    "identify the type of object the text appears on. Be literal and precise."
)

OBJECT_TYPE_HINTS = [
    "Class 1 – Chemicals",
    "Class 2 – Paints",
    "Class 3 – Cosmetics and cleaning preparations",
    "Class 4 – Lubricants and fuels",
    "Class 5 – Pharmaceuticals",
    "Class 6 – Metal goods",
    "Class 7 – Machinery",
    "Class 8 – Hand tools",
    "Class 9 – Electrical and scientific apparatus",
    "Class 10 – Medical apparatus",
    "Class 11 – Environmental control apparatus",
    "Class 12 – Vehicles",
    "Class 13 – Firearms",
    "Class 14 – Jewelry",
    "Class 15 – Musical instruments",
    "Class 16 – Paper goods and printed matter",
    "Class 17 – Rubber goods",
    "Class 18 – Leather goods",
    "Class 19 – Non-metallic building materials",
    "Class 20 – Furniture and articles not otherwise classified",
    "Class 21 – Housewares and glass",
    "Class 22 – Cordage and fibers",
    "Class 23 – Yarns and threads",
    "Class 24 – Fabrics",
    "Class 25 – Clothing",
    "Class 26 – Fancy goods",
    "Class 27 – Floor coverings",
    "Class 28 – Toys and sporting goods",
    "Class 29 – Meats and processed foods",
    "Class 30 – Staple foods",
    "Class 31 – Natural agricultural products",
    "Class 32 – Light beverages",
    "Class 33 – Wines and spirits",
    "Class 34 – Smokers’ articles"
]

GENERATION_CONFIG = {
    "response_mime_type": "application/json",
    "temperature": 0.2,
}

# Vision model with system instructions for OCR + classification
model = get_model(
    MODEL_ID,
    system_instruction=SYSTEM_INSTRUCTIONS,
)

PROMPT_TEMPLATE = f"""
Task:
1) Read *all* visible text (OCR).
2) Classify the type of object the text is printed on or displayed on.

Guidelines:
- Always select exactly one class from this list:
{OBJECT_TYPE_HINTS}
- Keep punctuation and line breaks where helpful, however, put text in sentence format.
- If text is partially obscured, include what you can read and note uncertainty.
- If multiple objects are present, choose the one with the **main** text.

Output strictly as JSON with this schema:
{{
  "text": "string: all extracted text",
  "object_type": "string: a phrase from the list of objects given",
  "confidence": 0.0,
  "notes": "string: optional short notes about ambiguities"
}}
"""

router = APIRouter(prefix="/parser", tags=["parser"])

# Accepts an image file and returns text + Nice class as JSON.
@router.post("/v1/parse-image")
async def parse_image(image: UploadFile = File(...)):
    content_type = image.content_type or ""
    if not content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail=f"Unsupported content type: {content_type}")

    img_bytes = await image.read()
    if not img_bytes:
        raise HTTPException(status_code=400, detail="Empty image file")

    parts = [
        PROMPT_TEMPLATE,
        {"mime_type": content_type, "data": img_bytes},
    ]

    # First: OCR + object classification
    try:
        resp = model.generate_content(
            parts,
            generation_config=GENERATION_CONFIG,
            safety_settings=None,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM call failed: {e}")

    # Parse JSON from the model
    try:
        data = json.loads(resp.text)
        if not isinstance(data, dict):
            raise ValueError("Model returned non-dict JSON")
    except Exception:
        raise HTTPException(status_code=502, detail=f"Non-JSON model response: {resp.text!r}")

    # Ensure expected keys exist
    data.setdefault("text", "")
    data.setdefault("object_type", "")
    data.setdefault("confidence", 0.0)
    data.setdefault("notes", "")

    # Grab the cleaned values
    text = data.get("text", "")
    object_type = data.get("object_type", "")

    # --- NEW: generate a listing-style description using the text + object type ---
    description = ""
    try:
        desc_model = get_model(MODEL_ID)

        desc_prompt = f"""
You are helping write an e-commerce listing.

Here is OCR text extracted from the product image:
{text}

Here is the Nice class / object type classification:
{object_type}

Write a short, shopper-friendly listing description (2–3 sentences) describing the product.
Do NOT include any brand names or trademarks. Focus on what the item is, its materials,
its purpose, style, and key features. Keep it suitable for a generic online marketplace.

Example style:
"Hand-stitched leather journal with recycled paper, A5 size. Personalized engraving available.
Minimalist travel notebook for writers & artists."

Now generate the listing description:
"""

        desc_resp = desc_model.generate_content(desc_prompt)
        description = (getattr(desc_resp, "text", "") or "").strip()
    except Exception:
        # If the description generation fails, don't kill the whole endpoint
        description = ""

    # Attach the description to the result JSON
    data["description"] = description

    return {
        "ok": True,
        "result": data,
        "meta": {
            "model": MODEL_ID,
            "content_type": content_type,
            "bytes": len(img_bytes),
        },
    }
