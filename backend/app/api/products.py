"""NutriGuide AI - Packaged Products & Allergens Router"""
import logging
from fastapi import APIRouter, Query, HTTPException
from app.services.openfoodfacts import search_product, get_product_by_barcode
from app.schemas.food import ProductInfo

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/products/search")
async def search_products(
    q: str = Query(..., min_length=1, max_length=100, description="Product name to search"),
    page_size: int = Query(5, ge=1, le=20),
):
    """Search Open Food Facts for packaged products."""
    cleaned_q = q.strip()
    if not cleaned_q:
        return {
            "results": [],
            "message": "Search query cannot be empty.",
        }
    results = await search_product(cleaned_q, page_size=page_size)
    if not results:
        return {
            "results": [],
            "message": (
                f"No products found for '{cleaned_q}' in Open Food Facts. "
                "Try a different search term or search by barcode."
            ),
        }
    return {"results": [r.model_dump() for r in results]}


@router.get("/products/barcode/{barcode}", response_model=ProductInfo)
async def get_product_by_barcode_endpoint(barcode: str):
    """Get product information by barcode from Open Food Facts."""
    clean_barcode = barcode.strip()
    if not clean_barcode.isdigit() or len(clean_barcode) < 6 or len(clean_barcode) > 32:
        raise HTTPException(
            status_code=400,
            detail="Barcode must be numeric and between 6 and 32 digits in length."
        )
    result = await get_product_by_barcode(clean_barcode)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Product with barcode '{clean_barcode}' not found in Open Food Facts."
        )
    return result
