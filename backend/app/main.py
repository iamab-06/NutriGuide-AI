"""
NutriGuide AI - FastAPI Main Application
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import analyze, nutrition, products, chat, compare, health, health_advisor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    logger.info("Starting NutriGuide AI backend...")
    # Pre-load classifier
    try:
        from app.services.classifier import get_classifier
        get_classifier()
        logger.info("Food classifier loaded.")
    except Exception as e:
        logger.warning(f"Could not pre-load classifier: {e}")

    # Pre-load RAG service and FAISS embeddings to eliminate cold-start latency spikes
    try:
        from app.rag.rag_service import get_rag_service
        rag = get_rag_service()
        rag.initialize()
        logger.info("RAG knowledge base and FAISS vector embeddings preloaded.")
    except Exception as e:
        logger.warning(f"Could not pre-load RAG service: {e}")

    # Pre-load Curated Local Food Database
    try:
        from app.data.food_database import get_local_food_db
        get_local_food_db()
        logger.info("Curated Local Food Database loaded.")
    except Exception as e:
        logger.warning(f"Could not pre-load local food database: {e}")

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
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS", "HEAD"],
    allow_headers=["Content-Type", "Authorization", "Accept", "X-Requested-With"],
)

# Include routers
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(analyze.router, prefix="/api", tags=["analyze"])
app.include_router(nutrition.router, prefix="/api", tags=["nutrition"])
app.include_router(products.router, prefix="/api", tags=["products"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(compare.router, prefix="/api", tags=["compare"])
app.include_router(health_advisor.router, prefix="/api/health-advisor", tags=["health-advisor"])


@app.get("/")
async def root():
    return {
        "app": "NutriGuide AI",
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs",
    }
