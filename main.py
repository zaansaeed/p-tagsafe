from dotenv import load_dotenv
load_dotenv() 

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from ranking_api import router as ranking_router
from parser_and_classifier_api import router as parser_router
from tag_generator_api import router as tag_generator_router
from aggregator_api import router as aggregator_router
from tmcheck_api import router as tmcheck_router

import os

app = FastAPI(
    title="TradeMark Checker API",
    description="An API suite for product classification, tag generation, and trademark analysis."
)

# Add CORS middleware to allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)
@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/", tags=["Home"])
def home():
    """Serve the frontend HTML page"""
    return FileResponse("frontend_html_css_js/index.html")

# Include all API routers
app.include_router(tag_generator_router)
app.include_router(ranking_router)
app.include_router(parser_router)
app.include_router(aggregator_router)
app.include_router(tmcheck_router)
