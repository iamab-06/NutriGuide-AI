"""
NutriGuide AI - Clinical Condition Health Advisor API Router
Provides endpoints to list supported medical/dietary conditions and
evaluate any food or plate against active health profiles.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.clinical_advisor import (
    AVAILABLE_CONDITIONS,
    evaluate_food_health_safety,
)
from app.services.nutrition import get_nutrition_for_food
from app.schemas.food import HealthSafetyReport, NutritionData

logger = logging.getLogger(__name__)
router = APIRouter()


class ConditionItem(BaseModel):
    id: str
    name: str
    category: str
    icon: str
    description: str


class EvaluateHealthRequest(BaseModel):
    food_name: str = Field(..., min_length=1, max_length=100)
    category_key: Optional[str] = None
    nutrition: Optional[NutritionData] = None
    conditions: List[str] = Field(default_factory=list)
    portion_g: float = Field(default=100.0, ge=1.0, le=2000.0)


@router.get("/conditions", response_model=List[ConditionItem])
async def get_supported_conditions():
    """
    Get the list of supported medical conditions and dietary restrictions
    available for clinical screening in NutriGuide AI.
    """
    return AVAILABLE_CONDITIONS


@router.post("/evaluate", response_model=HealthSafetyReport)
async def evaluate_food_safety(request: EvaluateHealthRequest):
    """
    Evaluate a food item against selected clinical conditions
    (e.g., Diabetes, Hypertension, High Cholesterol, Gout, Celiac, Lactose).
    If nutrition is not provided, automatically retrieves it from the knowledge base.
    """
    food_name = request.food_name.strip()
    nutrition = request.nutrition

    if not nutrition:
        try:
            nutrition = await get_nutrition_for_food(
                food_name=food_name,
                category_key=request.category_key,
            )
        except Exception as e:
            logger.warning(f"Could not retrieve nutrition for {food_name}: {e}")
            nutrition = None

    report = evaluate_food_health_safety(
        food_name=food_name,
        nutrition=nutrition,
        conditions=request.conditions,
        portion_g=request.portion_g,
    )
    return report
