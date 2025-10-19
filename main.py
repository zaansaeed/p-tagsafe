from fastapi import FastAPI
from ranking_api import router as ranking_router

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Hello FastAPI!"}

app.include_router(ranking_router)