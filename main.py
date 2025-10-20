from fastapi import FastAPI
from ranking_api import router as ranking_router
from parser_and_classifier_api import router as parser_router
from tag_generator_api import router as tag_generator_router # Import the new router

app = FastAPI(
    title="TradeMark Checker API",
    description="An API suite for product classification, tag generation, and trademark analysis."
)

@app.get("/", tags=["Home"])
def home():
    return {"message": "Welcome to the TradeMark Checker API!"}

# Include the new tag generator router into the main application
app.include_router(tag_generator_router)

# Include your existing routers
app.include_router(ranking_router)
app.include_router(parser_router)
