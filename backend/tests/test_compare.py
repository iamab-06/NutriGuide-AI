"""
Tests for Food Comparison API
"""
import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.schemas.food import NutritionData, NutrientInfo


@pytest.mark.asyncio
async def test_compare_endpoint_success():
    food1_data = NutritionData(
        food_name="Pizza, cheese",
        source="USDA FoodData Central",
        calories=266.0,
        protein=10.5,
        carbohydrates=33.2,
        fat=9.8,
        sugar=3.6,
        fiber=2.3,
        sodium=598.0,
        data_available=True,
    )
    food2_data = NutritionData(
        food_name="Hamburger, single patty",
        source="USDA FoodData Central",
        calories=295.0,
        protein=17.0,
        carbohydrates=24.0,
        fat=14.0,
        sugar=4.0,
        fiber=1.5,
        sodium=480.0,
        data_available=True,
    )

    with patch("app.api.compare.get_nutrition_for_food", new_callable=AsyncMock) as mock_get, \
         patch("app.api.compare.chat_with_context", new_callable=AsyncMock) as mock_chat:

        mock_get.side_effect = [food1_data, food2_data]
        mock_chat.return_value = {
            "answer": "Pizza has fewer calories and fat, while hamburger offers more protein.",
            "sources": ["USDA FoodData Central"],
            "evidence_used": True
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post("/api/compare", json={"food1": "pizza", "food2": "hamburger"})

        assert response.status_code == 200
        data = response.json()
        assert data["food1"]["calories"] == 266.0
        assert data["food2"]["protein"] == 17.0
        assert data["basis"] == "per 100g"
        assert "Pizza has fewer calories" in data["ai_summary"]


@pytest.mark.asyncio
async def test_compare_endpoint_validation():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/compare", json={"food1": "", "food2": "pizza"})
    assert response.status_code == 400
