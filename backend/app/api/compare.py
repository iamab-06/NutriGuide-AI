"""NutriGuide AI - Food Comparison Router"""
import logging
from fastapi import APIRouter, HTTPException
from app.services.nutrition import get_nutrition_for_food
from app.services.gemini_service import chat_with_context
from app.schemas.food import CompareRequest, CompareResponse, NutritionData

logger = logging.getLogger(__name__)
router = APIRouter()


def _make_comparison_prompt(food1: NutritionData, food2: NutritionData) -> str:
    def fmt(val, unit):
        return f"{val} {unit}" if val is not None else "N/A"

    return (
        f"Compare these two foods nutritionally (all values per 100g from USDA FoodData Central):\n\n"
        f"{food1.food_name}:\n"
        f"  Calories: {fmt(food1.calories, 'kcal')}, Protein: {fmt(food1.protein, 'g')}, "
        f"Carbs: {fmt(food1.carbohydrates, 'g')}, Fat: {fmt(food1.fat, 'g')}, "
        f"Sugar: {fmt(food1.sugar, 'g')}, Fiber: {fmt(food1.fiber, 'g')}, "
        f"Sodium: {fmt(food1.sodium, 'mg')}\n\n"
        f"{food2.food_name}:\n"
        f"  Calories: {fmt(food2.calories, 'kcal')}, Protein: {fmt(food2.protein, 'g')}, "
        f"Carbs: {fmt(food2.carbohydrates, 'g')}, Fat: {fmt(food2.fat, 'g')}, "
        f"Sugar: {fmt(food2.sugar, 'g')}, Fiber: {fmt(food2.fiber, 'g')}, "
        f"Sodium: {fmt(food2.sodium, 'mg')}\n\n"
        "Provide a brief, factual comparison (under 150 words). "
        "Do not declare one food universally healthier. "
        "Note which values are not available (N/A). "
        "Use only the data provided above."
    )


@router.post("/compare", response_model=CompareResponse)
async def compare_foods(request: CompareRequest):
    """Compare nutrition data for two foods."""
    if not request.food1.strip() or not request.food2.strip():
        raise HTTPException(status_code=400, detail="Both food names are required.")

    # Fetch nutrition for both foods in parallel
    import asyncio
    try:
        food1_data, food2_data = await asyncio.gather(
            get_nutrition_for_food(request.food1),
            get_nutrition_for_food(request.food2),
        )
    except Exception as e:
        logger.error(f"Comparison nutrition fetch error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve nutrition data for comparison.")

    if food1_data is None:
        raise HTTPException(status_code=404, detail=f"No data found for '{request.food1}'.")
    if food2_data is None:
        raise HTTPException(status_code=404, detail=f"No data found for '{request.food2}'.")

    # Generate AI comparison summary
    ai_summary = None
    try:
        prompt = _make_comparison_prompt(food1_data, food2_data)
        result = await chat_with_context(user_message=prompt)
        ai_summary = result.get("answer")
    except Exception as e:
        logger.warning(f"AI comparison summary failed: {e}")
        ai_summary = "AI comparison summary unavailable."

    notes = []
    if not food1_data.data_available:
        notes.append(f"Nutrition data not available for {request.food1}.")
    if not food2_data.data_available:
        notes.append(f"Nutrition data not available for {request.food2}.")

    return CompareResponse(
        food1=food1_data,
        food2=food2_data,
        basis="per 100g",
        comparison_notes=" ".join(notes) if notes else None,
        ai_summary=ai_summary,
    )
