"""
NutriGuide AI - Unified Nutrition Service with Caching and Validation
=====================================================================
Retrieves verified nutritional data from:
1. Curated Local Food Database (instant <1ms, Indian staples + global whole foods)
2. In-Memory Async TTL Cache (single-flight deduplication)
3. USDA FoodData Central REST API (SR Legacy & Foundation Foods)
4. Numerical Validation Layer (Atwater 4-4-9 factor check, bounds sanitization)
"""
import logging
import math
from typing import Optional, Dict, Any, List
import httpx

from app.core.config import settings
from app.core.categories import USDA_SEARCH_QUERIES, CATEGORY_DISPLAY_NAMES, USDA_REFERENCE_DATA
from app.schemas.food import NutritionData, NutrientInfo, FoodSearchResult
from app.data.food_database import get_local_food_db
from app.services.cache import nutrition_cache, search_cache
from app.services.validator import validate_and_sanitize_nutrition

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
    """Extract and sanitize standard nutrients from a USDA food item."""
    nutrients_raw = food_item.get("foodNutrients", [])
    nutrient_map: Dict[int, float] = {}
    for n in nutrients_raw:
        nid = n.get("nutrientId") or (n.get("nutrient", {}).get("id"))
        amount = n.get("amount") or n.get("value")
        if nid is not None and amount is not None:
            try:
                f_amount = float(amount)
                if not math.isnan(f_amount) and not math.isinf(f_amount):
                    nutrient_map[int(nid)] = max(0.0, round(f_amount, 2))
            except (ValueError, TypeError):
                continue

    result = {}
    for key, nid in NUTRIENT_IDS.items():
        result[key] = nutrient_map.get(nid)
    return result


async def search_food(query: str, page_size: int = 5) -> List[FoodSearchResult]:
    """Search for foods matching query across Local DB and USDA FoodData Central with caching."""
    q_clean = query.strip().lower()
    cache_key = f"search_{q_clean}_{page_size}"
    cached_results = await search_cache.get(cache_key)
    if cached_results is not None:
        return cached_results

    results: List[FoodSearchResult] = []

    # 1. Check Local Curated Database first
    local_db = get_local_food_db()
    local_match = local_db.search_by_term(q_clean)
    if local_match:
        results.append(FoodSearchResult(
            fdcId=hash(local_match["id"]) % 10000000,
            description=local_match["canonical_name"],
            food_category=local_match["category"],
            brand_owner=None,
            score=100.0,
        ))

    # 2. Query USDA FoodData Central (supports Foundation, SR Legacy, and Survey FNDDS)
    try:
        search_payload = {
            "query": query,
            "dataType": ["Foundation", "SR Legacy", "Survey (FNDDS)"],
            "pageSize": page_size,
        }
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.post(
                f"{USDA_BASE_URL}/foods/search",
                params={"api_key": settings.usda_api_key},
                json=search_payload,
            )
            if response.status_code != 200:
                # Fallback to simple GET
                response = await client.get(
                    f"{USDA_BASE_URL}/foods/search",
                    params={"query": query, "pageSize": page_size, "api_key": settings.usda_api_key},
                )
            if response.status_code == 200:
                data = response.json()
                for f in data.get("foods", []):
                    results.append(FoodSearchResult(
                        fdcId=f.get("fdcId", 0),
                        description=f.get("description", ""),
                        food_category=f.get("foodCategory"),
                        brand_owner=f.get("brandOwner"),
                        score=f.get("score"),
                    ))
    except Exception as e:
        logger.warning(f"USDA search API query encountered issue: {e}")

    # 3. Fallback matching against standard categories if no results
    if not results:
        for cat_key, ref in USDA_REFERENCE_DATA.items():
            disp = CATEGORY_DISPLAY_NAMES.get(cat_key, "").lower()
            desc = ref.get("food_name", "").lower()
            if q_clean in cat_key or q_clean in disp or q_clean in desc or cat_key in q_clean:
                results.append(FoodSearchResult(
                    fdcId=ref["fdcId"],
                    description=ref["food_name"],
                    food_category="USDA Standard Reference",
                    brand_owner=None,
                    score=100.0,
                ))

    # Cache and return
    await search_cache.set(cache_key, results, ttl_sec=3600)
    return results


async def get_nutrition_by_fdcid(fdc_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve full nutrition details for a specific FDC ID with caching."""
    cache_key = f"fdc_{fdc_id}"
    cached = await nutrition_cache.get(cache_key)
    if cached is not None:
        return cached

    params = {"api_key": settings.usda_api_key}
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.get(f"{USDA_BASE_URL}/food/{fdc_id}", params=params)
            if response.status_code == 200:
                data = response.json()
                await nutrition_cache.set(cache_key, data, ttl_sec=86400)
                return data
    except Exception as e:
        logger.warning(f"USDA get food by FDC ID {fdc_id} error: {e}")

    # Fallback to local reference data by FDC ID
    for cat_key, ref in USDA_REFERENCE_DATA.items():
        if ref.get("fdcId") == fdc_id:
            logger.info(f"Using USDA Reference Data fallback for FDC ID {fdc_id}")
            nutrients = []
            for k, nid in NUTRIENT_IDS.items():
                if k in ref and ref[k] is not None:
                    nutrients.append({"nutrientId": nid, "amount": ref[k]})
            return {
                "description": ref["food_name"],
                "fdcId": fdc_id,
                "foodNutrients": nutrients,
                "source": "USDA FoodData Central (Standard Reference)",
            }

    return None


async def get_nutrition_for_food(food_name: str, category_key: Optional[str] = None) -> Optional[NutritionData]:
    """
    Retrieve validated nutrition for any food name.
    1. Checks Local Food Database (instant <1ms).
    2. Checks in-memory cache.
    3. Calls USDA API with validation & sanitization.
    """
    cleaned_name = food_name.strip()
    lookup_term = category_key if category_key else cleaned_name
    cache_key = f"food_nutr_{lookup_term.lower()}"

    cached = await nutrition_cache.get(cache_key)
    if cached is not None:
        return cached

    # Step 1: Check Local Curated Database first
    local_db = get_local_food_db()
    local_record = local_db.search_by_term(lookup_term)
    if not local_record and category_key:
        local_record = local_db.search_by_term(category_key)
    if not local_record:
        local_record = local_db.search_by_term(cleaned_name)

    if local_record:
        raw_dict = {
            "calories": local_record.get("calories"),
            "protein": local_record.get("protein"),
            "carbohydrates": local_record.get("carbohydrates"),
            "fat": local_record.get("fat"),
            "sugar": local_record.get("sugar"),
            "fiber": local_record.get("fiber"),
            "sodium": local_record.get("sodium"),
            "cholesterol": local_record.get("cholesterol"),
            "saturated_fat": local_record.get("saturated_fat"),
        }
        sanitized_dict, val_res = validate_and_sanitize_nutrition(
            raw_dict,
            basis="per 100g",
            source=local_record["source"],
            source_id=local_record.get("source_id"),
        )
        nutrient_list = [
            NutrientInfo(
                name=k.replace("_", " ").title(),
                amount=round(float(sanitized_dict[k]), 2),
                unit=NUTRIENT_UNITS.get(k, "g"),
            )
            for k in NUTRIENT_UNITS
            if sanitized_dict.get(k) is not None
        ]
        result = NutritionData(
            food_name=local_record["canonical_name"],
            source=local_record["source"],
            source_id=local_record.get("source_id"),
            basis="per 100g",
            calories=sanitized_dict.get("calories"),
            protein=sanitized_dict.get("protein"),
            carbohydrates=sanitized_dict.get("carbohydrates"),
            fat=sanitized_dict.get("fat"),
            sugar=sanitized_dict.get("sugar"),
            fiber=sanitized_dict.get("fiber"),
            sodium=sanitized_dict.get("sodium"),
            cholesterol=sanitized_dict.get("cholesterol"),
            saturated_fat=sanitized_dict.get("saturated_fat"),
            nutrients=nutrient_list,
            data_available=True,
            verification_status=val_res.verification_status,
            atwater_discrepancy_pct=val_res.atwater_discrepancy_pct,
            is_validated=val_res.is_valid,
            notes=local_record.get("portion_label"),
        )
        await nutrition_cache.set(cache_key, result, ttl_sec=86400)
        return result

    # Step 2: Query USDA Search
    query = USDA_SEARCH_QUERIES.get(category_key, cleaned_name) if category_key else cleaned_name
    search_results = await search_food(query, page_size=3)
    best = search_results[0] if search_results else None
    food_detail = await get_nutrition_by_fdcid(best.fdcId) if best else None

    # Step 3: Fallback to USDA_REFERENCE_DATA dictionary
    if not food_detail:
        ref_key = category_key if category_key in USDA_REFERENCE_DATA else None
        if not ref_key:
            for k in USDA_REFERENCE_DATA:
                if k in cleaned_name.lower().replace(" ", "_") or cleaned_name.lower() in k:
                    ref_key = k
                    break

        if ref_key and ref_key in USDA_REFERENCE_DATA:
            ref = USDA_REFERENCE_DATA[ref_key]
            raw_dict = {k: ref.get(k) for k in NUTRIENT_IDS}
            sanitized_dict, val_res = validate_and_sanitize_nutrition(
                raw_dict,
                basis="per 100g",
                source="USDA FoodData Central (Standard Reference)",
                source_id=str(ref.get("fdcId", "170000")),
            )
            nutrient_list = [
                NutrientInfo(
                    name=k.replace("_", " ").title(),
                    amount=round(float(sanitized_dict[k]), 2),
                    unit=NUTRIENT_UNITS.get(k, "g"),
                )
                for k in NUTRIENT_UNITS
                if sanitized_dict.get(k) is not None
            ]
            result = NutritionData(
                food_name=ref["food_name"],
                fdcId=ref["fdcId"],
                source="USDA FoodData Central (Standard Reference)",
                source_id=str(ref.get("fdcId")),
                basis="per 100g",
                calories=sanitized_dict.get("calories"),
                protein=sanitized_dict.get("protein"),
                carbohydrates=sanitized_dict.get("carbohydrates"),
                fat=sanitized_dict.get("fat"),
                sugar=sanitized_dict.get("sugar"),
                fiber=sanitized_dict.get("fiber"),
                sodium=sanitized_dict.get("sodium"),
                cholesterol=sanitized_dict.get("cholesterol"),
                saturated_fat=sanitized_dict.get("saturated_fat"),
                nutrients=nutrient_list,
                data_available=True,
                verification_status=val_res.verification_status,
                atwater_discrepancy_pct=val_res.atwater_discrepancy_pct,
                is_validated=val_res.is_valid,
            )
            await nutrition_cache.set(cache_key, result, ttl_sec=86400)
            return result

        return NutritionData(
            food_name=cleaned_name,
            data_available=False,
            notes=f"No verified nutrition records found for '{cleaned_name}'.",
        )

    # Step 4: Extract and Validate from live USDA food detail
    raw_nutrients = _extract_nutrients(food_detail)
    sanitized_nutrients, val_res = validate_and_sanitize_nutrition(
        raw_nutrients,
        basis="per 100g",
        source="USDA FoodData Central",
        source_id=str(best.fdcId),
    )

    nutrient_list = [
        NutrientInfo(
            name=k.replace("_", " ").title(),
            amount=round(float(sanitized_nutrients[k]), 2),
            unit=NUTRIENT_UNITS.get(k, "g"),
        )
        for k in NUTRIENT_UNITS
        if sanitized_nutrients.get(k) is not None
    ]

    result = NutritionData(
        food_name=best.description,
        fdcId=best.fdcId,
        source="USDA FoodData Central",
        source_id=str(best.fdcId),
        basis="per 100g",
        calories=sanitized_nutrients.get("calories"),
        protein=sanitized_nutrients.get("protein"),
        carbohydrates=sanitized_nutrients.get("carbohydrates"),
        fat=sanitized_nutrients.get("fat"),
        sugar=sanitized_nutrients.get("sugar"),
        fiber=sanitized_nutrients.get("fiber"),
        sodium=sanitized_nutrients.get("sodium"),
        cholesterol=sanitized_nutrients.get("cholesterol"),
        saturated_fat=sanitized_nutrients.get("saturated_fat"),
        nutrients=nutrient_list,
        data_available=True,
        verification_status=val_res.verification_status,
        atwater_discrepancy_pct=val_res.atwater_discrepancy_pct,
        is_validated=val_res.is_valid,
    )

    await nutrition_cache.set(cache_key, result, ttl_sec=86400)
    return result
