import os
import google.generativeai as genai
import re
from dotenv import load_dotenv




load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")


temperature = 0
n_output = 50


genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.5-flash-lite")








def preprocess_title(title):
   title = title.strip()
   title = re.sub(r"\s+", " ", title) 
   title = re.sub(r"\s+[,.:;!?-]+\s*$", "", title)
   return title
  


def generating_phrases (title):
 title = preprocess_title(title)


 prompt = f"""You are an assistant that writes short and descriptive phrases (3-4 words) for e-commerce listings.
 Title: “{title}”


 Instructions:
 - Output exactly {n_output} unique phrases
 - Each phrase must be 3 to 4 words long
 - Avoid brand name and trademarked terms"""




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


for title in etsy_titles:
   print(f"\nTitle: {title}")
   output = generating_phrases(title)
   print(output)



