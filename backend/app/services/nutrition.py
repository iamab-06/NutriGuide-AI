"""
NutriGuide AI - USDA FoodData Central Nutrition Service
"""
import logging
from typing import Optional, Dict, Any, List
import httpx
from app.core.config import settings
from app.core.categories import USDA_SEARCH_QUERIES, CATEGORY_DISPLAY_NAMES, USDA_REFERENCE_DATA
from app.schemas.food import NutritionData, NutrientInfo, FoodSearchResult

logger = logging.getLogger(__name__)

USDA_BASE_URL = "https://api.nal.usda.gov/fdc/v1"

# Nutrient IDs in USDA FoodData Central
NUTRIENT_IDS = {
    "calories": 1008,       # Energy (kcal)
    "protein": 1003,        # Protein
    "carbohydrates": 1005,  # Carbohydrate, by difference
    "fat": 1004,            # Total lipid (fat)
    "sugar": 2000,          # Sugars, total
    "fiber": 1079,          # Fiber, total dietary
    "sodium": 1093,         # Sodium
    "cholesterol": 1253,    # Cholesterol
    "saturated_fat": 1258,  # Fatty acids, total saturated
}

NUTRIENT_UNITS = {
    "calories": "kcal",
    "protein": "g",
    "carbohydrates": "g",
    "fat": "g",
    "sugar": "g",
    "fiber": "g",
    "sodium": "mg",
    "cholesterol": "mg",
    "saturated_fat": "g",
}


def _extract_nutrients(food_item: Dict[str, Any]) -> Dict[str, Optional[float]]:
    """Extract standard nutrients from a USDA food item."""
    nutrients_raw = food_item.get("foodNutrients", [])
    nutrient_map: Dict[int, float] = {}
    for n in nutrients_raw:
        nid = n.get("nutrientId") or (n.get("nutrient", {}).get("id"))
        amount = n.get("amount") or n.get("value")
        if nid and amount is not None:
            nutrient_map[int(nid)] = float(amount)

    result = {}
    for key, nid in NUTRIENT_IDS.items():
        result[key] = nutrient_map.get(nid)
    return result


async def search_food(query: str, page_size: int = 5) -> List[FoodSearchResult]:
    """Search USDA FoodData Central for foods matching query."""
    params = {
        "query": query,
        "dataType": ["Foundation", "SR Legacy"],
        "pageSize": page_size,
        "api_key": settings.usda_api_key,
    }
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(f"{USDA_BASE_URL}/foods/search", params=params)
            response.raise_for_status()
            data = response.json()
    except httpx.TimeoutException:
        logger.error("USDA API timeout")
        return []
    except httpx.HTTPStatusError as e:
        logger.error(f"USDA API HTTP error: {e.response.status_code}")
        return []
    except Exception as e:
        logger.error(f"USDA API error: {e}")
        return []

    foods = data.get("foods", [])
    results = []
    for f in foods:
        results.append(FoodSearchResult(
            fdcId=f.get("fdcId", 0),
            description=f.get("description", ""),
            food_category=f.get("foodCategory"),
            brand_owner=f.get("brandOwner"),
            score=f.get("score"),
        ))
    return results


async def get_nutrition_by_fdcid(fdc_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve full nutrition details for a specific FDC ID."""
    params = {"api_key": settings.usda_api_key}
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(f"{USDA_BASE_URL}/food/{fdc_id}", params=params)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"USDA get food error (fdcId={fdc_id}): {e}")
        return None


async def get_nutrition_for_food(food_name: str, category_key: Optional[str] = None) -> Optional[NutritionData]:
    """
    Retrieve nutrition for a food name.
    Uses category key to select the best USDA search query.
    """
    # Determine search query
    if category_key and category_key in USDA_SEARCH_QUERIES:
        query = USDA_SEARCH_QUERIES[category_key]
    else:
        query = food_name

    results = await search_food(query, page_size=3)
    best = results[0] if results else None
    food_detail = await get_nutrition_by_fdcid(best.fdcId) if best else None

    # Fallback to verified USDA reference dataset if live API is unavailable or rate-limited
    if not food_detail:
        lookup_key = category_key if category_key in USDA_REFERENCE_DATA else None
        if not lookup_key:
            for k in USDA_REFERENCE_DATA:
                if k in food_name.lower().replace(" ", "_") or food_name.lower() in k:
                    lookup_key = k
                    break

        if lookup_key and lookup_key in USDA_REFERENCE_DATA:
            ref = USDA_REFERENCE_DATA[lookup_key]
            logger.info(f"Using USDA Reference Data fallback for '{food_name}' ({lookup_key})")
            nutrient_list = []
            for k, val in ref.items():
                if k in NUTRIENT_UNITS and val is not None:
                    nutrient_list.append(NutrientInfo(
                        name=k.replace("_", " ").title(),
                        amount=round(float(val), 2),
                        unit=NUTRIENT_UNITS.get(k, ""),
                    ))
            return NutritionData(
                food_name=ref["food_name"],
                fdcId=ref["fdcId"],
                source="USDA FoodData Central (Standard Reference)",
                basis="per 100g",
                calories=ref.get("calories"),
                protein=ref.get("protein"),
                carbohydrates=ref.get("carbohydrates"),
                fat=ref.get("fat"),
                sugar=ref.get("sugar"),
                fiber=ref.get("fiber"),
                sodium=ref.get("sodium"),
                cholesterol=ref.get("cholesterol"),
                saturated_fat=ref.get("saturated_fat"),
                nutrients=nutrient_list,
                data_available=True,
            )

        return NutritionData(
            food_name=food_name,
            data_available=False,
            notes=f"No nutrition data found for '{food_name}' in USDA FoodData Central."
        )

    nutrients = _extract_nutrients(food_detail)

    # Build nutrient list
    nutrient_list = []
    for key, amount in nutrients.items():
        if amount is not None:
            nutrient_list.append(NutrientInfo(
                name=key.replace("_", " ").title(),
                amount=round(amount, 2),
                unit=NUTRIENT_UNITS.get(key, ""),
            ))

    return NutritionData(
        food_name=best.description,
        fdcId=best.fdcId,
        source="USDA FoodData Central",
        basis="per 100g",
        calories=nutrients.get("calories"),
        protein=nutrients.get("protein"),
        carbohydrates=nutrients.get("carbohydrates"),
        fat=nutrients.get("fat"),
        sugar=nutrients.get("sugar"),
        fiber=nutrients.get("fiber"),
        sodium=nutrients.get("sodium"),
        cholesterol=nutrients.get("cholesterol"),
        saturated_fat=nutrients.get("saturated_fat"),
        nutrients=nutrient_list,
        data_available=True,
    )
