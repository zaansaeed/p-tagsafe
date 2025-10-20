from dotenv import load_dotenv
load_dotenv() 

from fastapi import FastAPI
from ranking_api import router as ranking_router
from tmcheck_api import router as tmcheck_router  

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Hello FastAPI!"}

app.include_router(ranking_router)
app.include_router(tmcheck_router)  