from fastapi import FastAPI
from ranking_api import router as ranking_router
from parser_and_classifier_api import router as parser_router

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Hello FastAPI!"}

app.include_router(ranking_router)
app.include_router(parser_router)