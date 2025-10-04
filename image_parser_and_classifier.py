import os, json, sys
from typing import Dict, Any
from PIL import Image
import google.generativeai as genai

MODEL_ID = "gemini-2.5-flash-lite"
api_key = os.getenv("GOOGLE_API_KEY")

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

model = genai.GenerativeModel(
        MODEL_ID,
        system_instruction=SYSTEM_INSTRUCTIONS,
)
generation_config = {
        "response_mime_type": "application/json",
        "temperature": 0.2,
    }

img = Image.open("image.png")
PROMPT = f"""
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
resp = model.generate_content(
        [PROMPT, img],
        generation_config=generation_config,
        safety_settings=None,  # optional: rely on defaults
    )

data = json.loads(resp.text)
print(data)