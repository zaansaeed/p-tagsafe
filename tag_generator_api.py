import os
import re
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import google.generativeai as genai

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
MODEL_ID = "gemini-2.5-flash-lite"
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise RuntimeError("Missing GOOGLE_API_KEY environment variable.")

# Configure the generative AI model
try:
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel(MODEL_ID)
except Exception as e:
    # Handle potential configuration errors, e.g., invalid API key
    raise RuntimeError(f"Failed to configure Google Generative AI: {e}")

# --- API Setup ---
router = APIRouter(prefix="/tags", tags=["tags"])

class TagGenerationRequest(BaseModel):
    """Defines the input structure for the tag generation request."""
    nice_class: int = Field(..., description="The Nice Classification code for the product (e.g., 25 for apparel).")
    product_text: str = Field(default="", description="Any text printed directly on the product.")
    product_description: str = Field(..., description="A general description of the product.")
    
class TagGenerationResponse(BaseModel):
    """Defines the output structure, containing the list of generated tags."""
    tags: list[str]

# --- Core Logic ---
def generate_tags_from_llm(nice_class: int, product_text: str, product_description: str) -> list[str]:
    """
    Generates 50 marketable tags using the generative AI model.

    Args:
        nice_class: The product's Nice Classification code.
        product_text: Text found on the product image.
        product_description: A description of the product.

    Returns:
        A list of 50 generated tags.
    """
    # This detailed prompt guides the AI to generate relevant, concise, and marketable tags.
    prompt = f"""
    You are an expert e-commerce assistant specializing in SEO and product tagging.
    Your task is to generate exactly 50 marketable and descriptive tags for a product.

    Product Details:
    - **Nice Classification:** Class {nice_class}
    - **Product Description:** {product_description}
    - **Text on Product:** "{product_text}"

    Instructions:
    1.  **Tag Quantity:** Generate exactly 50 unique tags.
    2.  **Character Limit:** Each tag must be 20 characters or less. This is a strict limit.
    3.  **Relevance:** Tags must be highly relevant to the product description, the text on the product, and its Nice Class.
    4.  **Content Focus:** Incorporate keywords related to the product's style, theme, materials, target audience, and potential use cases. Use the "Text on Product" as a primary source of inspiration.
    5.  **Format:** Return the tags as a plain list, with each tag on a new line. Do not include numbers, bullet points, or any other formatting.

    Example for a Class 25 t-shirt with text "Best Dad":
    Best Dad Shirt
    Gift for Father
    Dad Birthday Gift
    Family Apparel
    Men's Graphic Tee
    Fathers Day Top
    Humor Dad T-Shirt
    #1 Dad Tee
    ... and so on for 50 tags.
    """

    try:
        response = model.generate_content(
            prompt,
            generation_config={"temperature": 0.7} # A higher temperature encourages more creative/diverse tags
        )
        
        # Process the response text to create a clean list of tags
        if not response.text:
            return []
            
        tags = [tag.strip() for tag in response.text.split('\n') if tag.strip()]
        # Filter again to ensure character limit is respected, as LLMs can sometimes miss instructions
        valid_tags = [tag for tag in tags if len(tag) <= 20]
        return valid_tags
        
    except Exception as e:
        print(f"An error occurred during LLM call: {e}")
        # In an API context, re-raise as HTTPException to inform the client
        raise HTTPException(status_code=500, detail=f"Failed to generate tags due to an internal error: {e}")


# --- API Endpoint ---
@router.post("/generate", response_model=TagGenerationResponse)
async def generate_marketable_tags(request: TagGenerationRequest):
    """
    API endpoint to generate 50 marketable tags based on product information.
    """
    tags = generate_tags_from_llm(
        nice_class=request.nice_class,
        product_text=request.product_text,
        product_description=request.product_description
    )
    
    if not tags:
        raise HTTPException(status_code=500, detail="Tag generation failed, model returned no content.")
        
    return TagGenerationResponse(tags=tags)

# --- Direct Execution for Testing ---
if __name__ == "__main__":
    """
    This block allows for direct testing of the script without running the full API.
    It uses a hardcoded example as requested.
    """
    print("--- Running Standalone Test ---")
    
    # Hardcoded example data for testing
    example_nice_class = 25
    example_product_text = "Best Dad"
    example_product_description = "A standard black t-shirt for men, celebrating fathers."
    
    print(f"Test Case: Nice Class='{example_nice_class}', Text='{example_product_text}'")
    
    try:
        # Call the core logic function directly
        generated_tags = generate_tags_from_llm(
            nice_class=example_nice_class,
            product_text=example_product_text,
            product_description=example_product_description
        )
        
        # Print the results
        if generated_tags:
            print(f"\nSuccessfully generated {len(generated_tags)} tags:")
            for i, tag in enumerate(generated_tags, 1):
                print(f"{i:2d}. {tag} (Length: {len(tag)})")
        else:
            print("\nGeneration failed. No tags were returned.")
            
    except Exception as e:
        print(f"\nAn error occurred during the test: {e}")
    
    print("\n--- Test Complete ---")
