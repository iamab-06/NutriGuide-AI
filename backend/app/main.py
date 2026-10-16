"""
NutriGuide AI - FastAPI Main Application
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import analyze, nutrition, products, chat, compare, health

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    logger.info("Starting NutriGuide AI backend...")
    # Pre-load the classifier
    try:
        from app.services.classifier import get_classifier
        get_classifier()
        logger.info("Food classifier loaded.")
    except Exception as e:
        logger.warning(f"Could not pre-load classifier: {e}")

    # Initialize RAG in background (lazy)
    logger.info("RAG service will initialize on first request.")
    yield
    logger.info("NutriGuide AI backend shutting down.")


app = FastAPI(
    title="NutriGuide AI",
    description="AI-powered nutrition analysis API",
    version=settings.app_version,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(analyze.router, prefix="/api", tags=["analyze"])
app.include_router(nutrition.router, prefix="/api", tags=["nutrition"])
app.include_router(products.router, prefix="/api", tags=["products"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(compare.router, prefix="/api", tags=["compare"])


@app.get("/")
async def root():
    return {
        "app": "NutriGuide AI",
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs",
    }
