from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from ranking_api import router as ranking_router
from parser_and_classifier_api import router as parser_router
from tag_generator_api import router as tag_generator_router # Import the new router
import os

app = FastAPI(
    title="TradeMark Checker API",
    description="An API suite for product classification, tag generation, and trademark analysis."
)

# Add CORS middleware to allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Mount static files
app.mount("/static", StaticFiles(directory="frontend_html_css_js"), name="static")

@app.get("/", tags=["Home"])
def home():
    """Serve the frontend HTML page"""
    return FileResponse("frontend_html_css_js/index.html")

# Include the new tag generator router into the main application
app.include_router(tag_generator_router)

# Include your existing routers
app.include_router(ranking_router)
app.include_router(parser_router)
