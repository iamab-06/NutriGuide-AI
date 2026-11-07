"""NutriGuide AI - Nutrition Information Router"""
import logging
from typing import Optional
from fastapi import APIRouter, Query, HTTPException
from app.services.nutrition import get_nutrition_for_food, search_food
from app.schemas.food import NutritionData

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/nutrition/search")
async def search_nutrition(
    q: str = Query(..., min_length=1, max_length=100, description="Food name to search")
):
    """Search for foods in USDA FoodData Central."""
    cleaned_q = q.strip()
    if not cleaned_q:
        return {"results": [], "message": "Search query cannot be empty."}
    results = await search_food(cleaned_q, page_size=10)
    if not results:
        return {"results": [], "message": f"No results found for '{cleaned_q}'."}
    return {"results": [r.model_dump() for r in results]}


@router.get("/nutrition/{food_name}", response_model=NutritionData)
async def get_nutrition(
    food_name: str,
    category_key: Optional[str] = Query(None, max_length=50, description="Internal category key for better matching"),
):
    """Get nutrition information for a food name."""
    cleaned_name = food_name.strip()
    if not cleaned_name or len(cleaned_name) > 100:
        raise HTTPException(status_code=400, detail="Food name must be between 1 and 100 characters.")
    try:
        data = await get_nutrition_for_food(
            food_name=cleaned_name,
            category_key=category_key.strip() if category_key else None,
        )
        if data is None:
            raise HTTPException(status_code=404, detail=f"No nutrition data found for '{cleaned_name}'.")
        return data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Nutrition lookup error: {e}")
        raise HTTPException(status_code=500, detail="Nutrition lookup failed. Please try again.")
