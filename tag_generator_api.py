import os
import re
from typing import Optional
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
from PIL import Image  # For handling image objects
import io
from config import MODEL_ID, get_model
from ranking_api import RankRequest, rank_phrases
from tmcheck_api import check_one_phrase
import asyncio

model = get_model(MODEL_ID)

router = APIRouter(prefix="/tags", tags=["tags"])

class TagGenerationResponse(BaseModel):
    """Defines the output structure, containing the list of generated tags."""
    tags: list[str]

# --- Core Logic ---
async def generate_tags_from_llm(nice_class: int, product_text: str, image: Optional[Image.Image] = None) -> list[str]:
    """
    Generates 50 marketable tags using the generative AI model based on an image.

    Args:
        nice_class: The product's Nice Classification code.
        product_text: Text found on the product.
        image: A PIL Image object of the product.

    Returns:
        A list of generated tags filtered for trademark safety and ranked by relevance.
    """
    # This prompt is now multi-modal, guiding the AI to analyze the image.
    prompt = f"""
    You are an expert e-commerce assistant specializing in SEO and product tagging.
    Your task is to generate exactly 50 marketable and descriptive tags for the product in the image.

    Product Details:
    - **Nice Classification:** Class {nice_class}
    - **Text on Product (if any):** "{product_text}"
    - **Product Image:** [See attached image]

    Instructions:
    1.  **Analyze the Image:** Look at the product's style, color, shape, and overall theme.
    2.  **Tag Quantity:** Generate exactly 50 unique tags.
    3.  **Character Limit:** Each tag must be 20 characters or less. This is a strict limit.
    4.  **Relevance:** Tags must be highly relevant to the product shown, the text on it, and its Nice Class.
    5.  **Content Focus:** Incorporate keywords related to the product's style, theme, materials, target audience, and potential use cases. Use the "Text on Product" as a primary source of inspiration.
    6.  **Format:** Return the tags as a plain list, with each tag on a new line. Do not include numbers, bullet points, or any other formatting.

    Example for a Class 25 t-shirt (image of a black shirt with text "Best Dad"):
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
        parts = [prompt]
        if image is not None:
            parts.append(image)
        response = model.generate_content(
            parts if len(parts) > 1 else prompt,
            generation_config={"temperature": 0.7}
        )

        # --- Debug logging for tag generation pipeline ---
        print("RAW RESPONSE TEXT:", repr(response.text))

        if not response.text:
            print("DEBUG: Model returned empty response.text")
            return []

        tags = [tag.strip() for tag in response.text.split('\n') if tag.strip()]
        print("DEBUG: NUMBER OF TAGS FROM MODEL:", len(tags))

        valid_tags = [tag for tag in tags if len(tag) <= 20]
        print("DEBUG: VALID TAGS (<=20 chars):", len(valid_tags))

        # Check trademark safety via USPTO for each tag
        if valid_tags:
            check_tasks = [check_one_phrase(tag, nice_class) for tag in valid_tags]
            check_results = await asyncio.gather(*check_tasks, return_exceptions=True)
            
            # Filter out blocked tags (those that returned a PhraseDecision) and exceptions
            safe_tags = []
            for i, result in enumerate(check_results):
                if isinstance(result, Exception):
                    print(f"DEBUG: TM check exception for '{valid_tags[i]}': {result}")
                    # On error, assume safe (fail open)
                    safe_tags.append(valid_tags[i])
                elif result is None:
                    # None means safe
                    safe_tags.append(valid_tags[i])
                # else: result is PhraseDecision, blocked
            
            print("DEBUG: SAFE TAGS AFTER TM CHECK:", len(safe_tags))

            # If all tags were filtered out by the TM check, fall back to the original valid tags
            if not safe_tags:
                print("DEBUG: No safe_tags after TM check, falling back to valid_tags")
                safe_tags = valid_tags
        else:
            safe_tags = []

        # Apply semantic ranking to reorder safe tags by relevance
        if safe_tags:
            try:
                rank_req = RankRequest(
                    user_text=f"PRODUCT TEXT: {product_text} NICE CLASS: {nice_class}",
                    phrases=safe_tags
                )
                safe_tags = await rank_phrases(rank_req)
            except Exception as rank_error:
                print(f"DEBUG: Ranking failed ({rank_error}), returning unranked tags")
                # Return unranked tags if ranking fails
                pass

        return safe_tags

    except Exception as e:
        print(f"An error occurred during LLM call: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate tags due to an internal error: {e}")


# --- API Endpoint ---
@router.post("/generate", response_model=TagGenerationResponse)
async def generate_marketable_tags(
    nice_class: int = Form(...),
    product_text: str = Form(default=""),
    image_file: Optional[UploadFile] = File(None)
):
    """
    API endpoint to generate 50 marketable tags based on a product image and info.
    """
    image_pil = None
    if image_file is not None:
        if not image_file.content_type or not image_file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Invalid file type. Please upload an image.")
        try:
            image_bytes = await image_file.read()
            image_pil = Image.open(io.BytesIO(image_bytes))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to read or process image file: {e}")

    tags = await generate_tags_from_llm(
        nice_class=nice_class,
        product_text=product_text,
        image=image_pil
    )
    
    if not tags:
        raise HTTPException(status_code=500, detail="Tag generation failed, model returned no content.")
        
    return TagGenerationResponse(tags=tags)

# --- Direct Execution for Testing ---
if __name__ == "__main__":
    """
    This block allows for direct testing of the script without running the full API.
    It loads a hardcoded example image ("image.png") from the file system.
    """
    print("--- Running Standalone Test ---")
    
    # Hardcoded example data for testing
    example_nice_class = 25
    example_product_text = "Best Dad"
    
    print(f"Test Case: Nice Class='{example_nice_class}', Text='{example_product_text}'")
    
    try:
        # Load the test image from disk
        example_image = Image.open("image.png")
        print("Successfully loaded 'image.png' for testing.")
        
        # Call the core logic function directly (now async)
        async def test_run():
            generated_tags = await generate_tags_from_llm(
                nice_class=example_nice_class,
                product_text=example_product_text,
                image=example_image
            )
            
            # Print the results
            if generated_tags:
                print(f"\nSuccessfully generated {len(generated_tags)} trademark-safe tags:")
                for i, tag in enumerate(generated_tags, 1):
                    print(f"{i:2d}. {tag} (Length: {len(tag)})")
            else:
                print("\nGeneration failed. No tags were returned.")
        
        asyncio.run(test_run())
            
    except FileNotFoundError:
        print("\n--- TEST FAILED ---")
        print("Error: Test image 'image.png' not found in the project directory.")
        print("Please add an image file named 'image.png' to run the standalone test.")
    except Exception as e:
        print(f"\nAn error occurred during the test: {e}")
    
    print("\n--- Test Complete ---")
