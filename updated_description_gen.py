import os
import re
from dotenv import load_dotenv
from config import get_model, MODEL_ID


load_dotenv()
# use centralized model from config; leaves core generation logic unchanged
model = get_model(MODEL_ID)
temperature = 0
n_output = 50




def preprocess_title(title):
    title = title.strip()
    title = re.sub(r"\s+", " ", title)  
    title = re.sub(r"\s+[,.:;!?-]+\s*$", "", title) 
    return title
    

def generating_phrases (title):
  title = preprocess_title(title)

  prompt = f"""You are an assistant that generates short, trademark-friendly, SEO-optimized keyword phrases for Etsy product listings.  
Your goal is to help Etsy sellers improve search visibility while ensuring compliance with Etsy’s rules and trademark law.  

Title: “{title}”

Instructions:
1. Output exactly 50 unique keyword phrases.  
2. Each phrase must be between 1 and 4 words long.  
3. Each phrase must appear on its own line with no numbering, bullets, or explanations.  
4. Do not include brand names, trademarks, or copyrighted terms.  
5. Do not use wording that implies affiliation with any company (e.g., “Disney-inspired”, “Nike-style”).  
6. Optimize for Etsy SEO by using natural buyer search terms that real shoppers would type into Etsy.  
7. Include keywords describing style, material, color, shape, function, occasion, and theme.  
8. Keep tone descriptive and aligned with Etsy’s marketplace guidelines.  

Examples of Good Phrases:  
- "retro soda jewelry"  
- "cartoon trip shirt"  
- "mini basketball planter"  

Examples of Bad Phrases:  
- "Coca-Cola earrings"  
- "Disneyland tee"  
- "Nike swoosh planter"  
"""


  response = model.generate_content(
    contents=prompt,
    generation_config={
            "temperature": temperature,
            "max_output_tokens": 800,
        }
    )
  
  return response.text



#example from etsy 
etsy_titles = ["Coca-Cola Earrings – Retro Soda Can Jewelry | Fun Gift for Coke Lovers & Pop Culture Fans", 
               "Personalized Disneyland tee shirt, Disneyworld shirt, Family Disney shirts, Custom Disney name shirt, Disney group shirt, Disney trip shirt",
              "plntrs - Nike Swoosh Skills Mini Basketball Planter - new ball with stand"
               ]





# prelim trademark scorer 
FAMOUS_MARKS = {
    "disney", "pixar", "marvel", "harry potter", "hogwarts",
    "nike", "adidas", "yeezy", "puma",
    "apple", "iphone", "ipad", "macbook",
    "coca-cola", "coke", "pepsi", "sprite",
    "minecraft", "fortnite", "roblox", "pokemon", "nintendo",
    "barbie", "lego", "hello kitty", "sanrio",
    "taylor swift", "swiftie", "swifties",
    "starbucks", "mcdonalds", "mcdonald's",
    "nba", "nfl", "mlb", "nhl", "fifa", "olympics",
    "tesla", "google", "instagram", "tiktok", "youtube",
}

def score_phrase(phrase):
    phrase_lower = phrase.lower()
    score = 10
    reasons = []

    # high risk if its a known trademark .
    for mark in FAMOUS_MARKS:
        if mark in phrase_lower:
            score = 90
            reasons.append("Contains a famous trademark")
            break

    
    if score <= 24:
        label, emoji = "safe", "✅"
    elif score <= 59:
        label, emoji = "caution", "⚠️"
    else:
        label, emoji = "high_risk", "❌"

    return {"phrase": phrase, "score": score, "label": label, "emoji": emoji, "reasons": reasons}


def label_and_filter_phrases(generated_text):
    phrases = [ln.strip() for ln in generated_text.splitlines() if ln.strip()]
    labeled = [score_phrase(p) for p in phrases]
    safe_only = [r for r in labeled if r["label"] == "safe"]
    return labeled, safe_only



for title in etsy_titles:
    print(f"\nTitle: {title}")
    output = generating_phrases(title)
    labeled, safe = label_and_filter_phrases(output)

    for r in labeled:
        print(f"{r['emoji']}  {r['phrase']}  (score={r['score']})")

    print("\nSAFE PHRASES:")
    for r in safe:
        print(f"- {r['phrase']}")






