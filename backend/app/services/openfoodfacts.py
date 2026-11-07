"""
NutriGuide AI - Open Food Facts Service
"""
import logging
from typing import Optional, List, Dict, Any
import httpx
from app.core.config import settings
from app.schemas.food import ProductInfo

logger = logging.getLogger(__name__)

OFF_HOSTS = [
    "https://world.openfoodfacts.net",
    "https://world.openfoodfacts.org",
]
DEFAULT_USER_AGENT = "NutriGuideAI - Web - Version 1.0 - https://github.com/nutriguide-ai"


async def search_product(query: str, page: int = 1, page_size: int = 5) -> List[ProductInfo]:
    """Search Open Food Facts by product name with host failover."""
    params = {
        "search_terms": query,
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "page": page,
        "page_size": page_size,
        "fields": "product_name,brands,ingredients_text,allergens,allergens_tags,nutriments,image_url,code",
    }
    headers = {"User-Agent": DEFAULT_USER_AGENT}

    data = None
    for host in OFF_HOSTS:
        url = f"{host}/cgi/search.pl"
        try:
            async with httpx.AsyncClient(timeout=12.0) as client:
                response = await client.get(url, params=params, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    break
                else:
                    logger.warning(f"Open Food Facts ({host}) returned status {response.status_code}")
        except httpx.TimeoutException:
            logger.warning(f"Open Food Facts timeout on {host}")
        except Exception as e:
            logger.warning(f"Open Food Facts error on {host}: {e}")

    if not data or not isinstance(data, dict):
        logger.error(f"Could not retrieve valid search results for '{query}' from Open Food Facts")
        return []

    products = data.get("products", [])
    if not isinstance(products, list):
        return []

    results = []
    for p in products:
        if not isinstance(p, dict):
            continue
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
            allergens_tags=p.get("allergens_tags") or [],
            nutriments=p.get("nutriments") if isinstance(p.get("nutriments"), dict) else None,
            image_url=p.get("image_url"),
            barcode=p.get("code"),
            data_complete=len(missing) == 0,
            missing_fields=missing,
        ))
    return results


async def get_product_by_barcode(barcode: str) -> Optional[ProductInfo]:
    """Get product info by barcode with host failover."""
    headers = {"User-Agent": DEFAULT_USER_AGENT}

    data = None
    for host in OFF_HOSTS:
        url = f"{host}/api/v2/product/{barcode}.json"
        try:
            async with httpx.AsyncClient(timeout=12.0) as client:
                response = await client.get(url, headers=headers)
                if response.status_code == 200:
                    raw_json = response.json()
                    if isinstance(raw_json, dict) and raw_json.get("status") == 1:
                        data = raw_json
                        break
        except Exception as e:
            logger.warning(f"Open Food Facts barcode lookup error on {host}: {e}")

    if not data or not isinstance(data, dict) or data.get("status") != 1:
        return None

    p = data.get("product")
    if not isinstance(p, dict):
        return None

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
        allergens_tags=p.get("allergens_tags") or [],
        nutriments=p.get("nutriments") if isinstance(p.get("nutriments"), dict) else None,
        image_url=p.get("image_url"),
        barcode=barcode,
        data_complete=len(missing) == 0,
        missing_fields=missing,
    )
