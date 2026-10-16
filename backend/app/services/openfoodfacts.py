"""
NutriGuide AI - Open Food Facts Service
"""
import logging
from typing import Optional, List, Dict, Any
import httpx
from app.core.config import settings
from app.schemas.food import ProductInfo

logger = logging.getLogger(__name__)

OFF_BASE_URL = "https://world.openfoodfacts.org"


async def search_product(query: str, page: int = 1, page_size: int = 5) -> List[ProductInfo]:
    """Search Open Food Facts by product name."""
    url = f"{OFF_BASE_URL}/cgi/search.pl"
    params = {
        "search_terms": query,
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "page": page,
        "page_size": page_size,
        "fields": "product_name,brands,ingredients_text,allergens,allergens_tags,nutriments,image_url,code",
    }
    headers = {"User-Agent": settings.openfoodfacts_user_agent}
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
    except httpx.TimeoutException:
        logger.error("Open Food Facts API timeout")
        return []
    except Exception as e:
        logger.error(f"Open Food Facts error: {e}")
        return []

    products = data.get("products", [])
    results = []
    for p in products:
        missing = []
        if not p.get("ingredients_text"):
            missing.append("ingredients")
        if not p.get("allergens"):
            missing.append("allergens")
        results.append(ProductInfo(
            product_name=p.get("product_name"),
            brands=p.get("brands"),
            ingredients_text=p.get("ingredients_text"),
            allergens=p.get("allergens"),
            allergens_tags=p.get("allergens_tags", []),
            nutriments=p.get("nutriments"),
            image_url=p.get("image_url"),
            barcode=p.get("code"),
            data_complete=len(missing) == 0,
            missing_fields=missing,
        ))
    return results


async def get_product_by_barcode(barcode: str) -> Optional[ProductInfo]:
    """Get product info by barcode."""
    url = f"{OFF_BASE_URL}/api/v2/product/{barcode}.json"
    headers = {"User-Agent": settings.openfoodfacts_user_agent}
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
    except Exception as e:
        logger.error(f"Open Food Facts barcode lookup error: {e}")
        return None

    if data.get("status") != 1:
        return None

    p = data.get("product", {})
    missing = []
    if not p.get("ingredients_text"):
        missing.append("ingredients")
    if not p.get("allergens"):
        missing.append("allergens")

    return ProductInfo(
        product_name=p.get("product_name"),
        brands=p.get("brands"),
        ingredients_text=p.get("ingredients_text"),
        allergens=p.get("allergens"),
        allergens_tags=p.get("allergens_tags", []),
        nutriments=p.get("nutriments"),
        image_url=p.get("image_url"),
        barcode=barcode,
        data_complete=len(missing) == 0,
        missing_fields=missing,
    )
