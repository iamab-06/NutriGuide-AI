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
    from app.core.categories import (
        CATEGORY_DISPLAY_NAMES,
        SUPPORTED_CATEGORIES,
        ALL_FOOD101_CATEGORIES,
        FOOD101_DISPLAY_NAMES,
    )
    return {
        "categories": SUPPORTED_CATEGORIES,
        "display_names": CATEGORY_DISPLAY_NAMES,
        "count": len(SUPPORTED_CATEGORIES),
        "total_food101_count": len(ALL_FOOD101_CATEGORIES),
        "all_categories": ALL_FOOD101_CATEGORIES,
        "all_display_names": FOOD101_DISPLAY_NAMES,
    }


@router.get("/cache/stats")
async def get_cache_stats():
    from app.services.cache import nutrition_cache, search_cache, product_cache
    return {
        "nutrition_cache": nutrition_cache.get_stats(),
        "search_cache": search_cache.get_stats(),
        "product_cache": product_cache.get_stats(),
    }
