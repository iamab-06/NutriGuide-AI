"""NutriGuide AI - Health check router"""
from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
    }


@router.get("/categories")
async def get_categories():
    from app.core.categories import CATEGORY_DISPLAY_NAMES, SUPPORTED_CATEGORIES
    return {
        "categories": SUPPORTED_CATEGORIES,
        "display_names": CATEGORY_DISPLAY_NAMES,
        "count": len(SUPPORTED_CATEGORIES),
    }
