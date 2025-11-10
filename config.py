import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise RuntimeError("Missing GOOGLE_API_KEY environment variable.")

# Configure the SDK once here
genai.configure(api_key=GOOGLE_API_KEY)

# Expose model IDs used across the project (duplicates OK for now)
MODEL_ID = "gemini-2.5-flash-lite"
EMB_MODEL_ID = "text-embedding-004"

def get_model(model_id: str, **kwargs):
    """
    Return a configured GenerativeModel instance.
    kwargs forwarded to genai.GenerativeModel if needed.
    """
    return genai.GenerativeModel(model_id, **kwargs)