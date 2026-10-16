"""
Tests for Open Food Facts product information and allergens
"""
import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.schemas.food import ProductInfo


@pytest.mark.asyncio
async def test_search_products_endpoint():
    mock_product = ProductInfo(
        product_name="Hazelnut Spread with Cocoa",
        brands="Nutella",
        ingredients_text="Sugar, Palm Oil, Hazelnuts (13%), Skimmed Milk Powder (8.7%), Fat-Reduced Cocoa (7.4%), Emulsifier: Lecithins (Soya), Vanillin.",
        allergens="en:soybeans,en:milk,en:nuts",
        allergens_tags=["en:soybeans", "en:milk", "en:nuts"],
        barcode="3017620422003",
        source="Open Food Facts",
        data_complete=True,
        missing_fields=[],
    )

    with patch("app.api.products.search_product", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = [mock_product]
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/api/products/search?q=nutella")

        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 1
        prod = data["results"][0]
        assert prod["brands"] == "Nutella"
        assert "en:milk" in prod["allergens_tags"]
        assert prod["data_complete"] is True


@pytest.mark.asyncio
async def test_barcode_lookup_endpoint():
    mock_product = ProductInfo(
        product_name="Oreo Cookies",
        brands="Nabisco",
        ingredients_text="Unbleached enriched flour, sugar, palm oil, cocoa, high fructose corn syrup, baking soda, salt, soy lecithin, chocolate, artificial flavor.",
        allergens="en:gluten,en:soybeans",
        allergens_tags=["en:gluten", "en:soybeans"],
        barcode="044000032029",
        source="Open Food Facts",
        data_complete=True,
        missing_fields=[],
    )

    with patch("app.api.products.get_product_by_barcode", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_product
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/api/products/barcode/044000032029")

        assert response.status_code == 200
        data = response.json()
        assert data["product_name"] == "Oreo Cookies"
        assert data["barcode"] == "044000032029"


@pytest.mark.asyncio
async def test_invalid_barcode_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/products/barcode/abc123xyz")
    assert response.status_code == 400
    assert "Barcode must be numeric" in response.json()["detail"]
