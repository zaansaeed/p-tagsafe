import os
import re
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
from PIL import Image  # For handling image objects
import io
from config import MODEL_ID, get_model

model = get_model(MODEL_ID)

router = APIRouter(prefix="/tags", tags=["tags"])

class TagGenerationResponse(BaseModel):
    """Defines the output structure, containing the list of generated tags."""
    tags: list[str]

# --- Core Logic ---
def generate_tags_from_llm(nice_class: int, product_text: str, image: Image.Image) -> list[str]:
    """
    Generates 50 marketable tags using the generative AI model based on an image.

    Args:
        nice_class: The product's Nice Classification code.
        product_text: Text found on the product.
        image: A PIL Image object of the product.

    Returns:
        A list of generated tags.
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
        # Pass both the text prompt and the image object to the model
        response = model.generate_content(
            [prompt, image], # Multi-modal input
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
async def generate_marketable_tags(
    nice_class: int = Form(...),
    product_text: str = Form(default=""),
    image_file: UploadFile = File(...)
):
    """
    API endpoint to generate 50 marketable tags based on a product image and info.
    """
    # Validate image file type
    if not image_file.content_type or not image_file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload an image.")

    try:
        # Read image bytes and open with PIL
        image_bytes = await image_file.read()
        image_pil = Image.open(io.BytesIO(image_bytes))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read or process image file: {e}")

    tags = generate_tags_from_llm(
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
        
        # Call the core logic function directly
        generated_tags = generate_tags_from_llm(
            nice_class=example_nice_class,
            product_text=example_product_text,
            image=example_image
        )
        
        # Print the results
        if generated_tags:
            print(f"\nSuccessfully generated {len(generated_tags)} tags:")
            for i, tag in enumerate(generated_tags, 1):
                print(f"{i:2d}. {tag} (Length: {len(tag)})")
        else:
            print("\nGeneration failed. No tags were returned.")
            
    except FileNotFoundError:
        print("\n--- TEST FAILED ---")
        print("Error: Test image 'image.png' not found in the project directory.")
        print("Please add an image file named 'image.png' to run the standalone test.")
    except Exception as e:
        print(f"\nAn error occurred during the test: {e}")
    
    print("\n--- Test Complete ---")

