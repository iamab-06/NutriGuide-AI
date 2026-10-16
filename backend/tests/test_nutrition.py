"""
Tests for Nutrition data services and endpoints
"""
import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.schemas.food import NutritionData, NutrientInfo
from app.services.nutrition import _extract_nutrients


def test_extract_nutrients_mapping():
    mock_usda_item = {
        "foodNutrients": [
            {"nutrientId": 1008, "amount": 266.0},
            {"nutrientId": 1003, "amount": 10.5},
            {"nutrientId": 1005, "amount": 33.2},
            {"nutrientId": 1004, "amount": 9.8},
            {"nutrientId": 2000, "amount": 3.6},
            {"nutrientId": 1079, "amount": 2.3},
            {"nutrientId": 1093, "amount": 598.0},
        ]
    }
    extracted = _extract_nutrients(mock_usda_item)
    assert extracted["calories"] == 266.0
    assert extracted["protein"] == 10.5
    assert extracted["carbohydrates"] == 33.2
    assert extracted["fat"] == 9.8
    assert extracted["sugar"] == 3.6
    assert extracted["fiber"] == 2.3
    assert extracted["sodium"] == 598.0


@pytest.mark.asyncio
async def test_get_nutrition_endpoint_mocked():
    mock_nutrition = NutritionData(
        food_name="Cheese Pizza",
        source="USDA FoodData Central",
        fdcId=12345,
        basis="per 100g",
        calories=266.0,
        protein=10.5,
        carbohydrates=33.2,
        fat=9.8,
        sugar=3.6,
        fiber=2.3,
        sodium=598.0,
        nutrients=[
            NutrientInfo(name="Calories", amount=266.0, unit="kcal"),
            NutrientInfo(name="Protein", amount=10.5, unit="g"),
        ],
        data_available=True
    )

    with patch("app.api.nutrition.get_nutrition_for_food", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_nutrition
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/api/nutrition/pizza")

        assert response.status_code == 200
        data = response.json()
        assert data["food_name"] == "Cheese Pizza"
        assert data["calories"] == 266.0
        assert data["basis"] == "per 100g"
        assert data["data_available"] is True


@pytest.mark.asyncio
async def test_search_nutrition_endpoint_mocked():
    from app.schemas.food import FoodSearchResult
    mock_results = [
        FoodSearchResult(fdcId=1001, description="Pizza, cheese", food_category="Fast Foods", score=100.0),
        FoodSearchResult(fdcId=1002, description="Pizza, pepperoni", food_category="Fast Foods", score=90.0),
    ]

    with patch("app.api.nutrition.search_food", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = mock_results
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/api/nutrition/search?q=pizza")

        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 2
        assert data["results"][0]["description"] == "Pizza, cheese"
