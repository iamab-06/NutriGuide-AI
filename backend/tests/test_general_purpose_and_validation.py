"""
NutriGuide AI - Tests for General-Purpose Expansion, Numerical Validation & Streaming
=====================================================================================
Validates:
1. Numerical Validation Layer (Atwater checks, bounds clamping, macro consistency).
2. Curated Local Food Database (120+ Indian and global foods).
3. Retrieval of foods beyond the original 20 categories.
4. Server-Sent Events (SSE) streaming endpoint structure.
5. In-Memory Caching efficiency and hit rates.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.services.validator import validate_and_sanitize_nutrition
from app.data.food_database import get_local_food_db
from app.services.nutrition import get_nutrition_for_food
from app.services.cache import nutrition_cache


def test_numerical_validator_bounds_and_atwater():
    """Test Atwater energy formula and physical bounds sanitization."""
    # Test 1: Valid macros with Atwater agreement
    # 20g Protein (80 kcal) + 30g Carbs (120 kcal) + 10g Fat (90 kcal) ≈ 290 kcal
    valid_food = {
        "calories": 290.0,
        "protein": 20.0,
        "carbohydrates": 30.0,
        "fat": 10.0,
        "sugar": 5.0,
        "fiber": 2.0,
        "sodium": 200.0,
    }
    sanitized, res = validate_and_sanitize_nutrition(valid_food, basis="per 100g", source="USDA Foundation")
    assert res.is_valid is True
    assert res.verification_status == "verified_lab"
    assert res.atwater_discrepancy_pct is not None
    assert res.atwater_discrepancy_pct < 10.0

    # Test 2: Negative numbers clamped to 0.0
    bad_food = {
        "calories": 100.0,
        "protein": -5.0,
        "carbohydrates": 20.0,
        "fat": 2.0,
    }
    sanitized, res = validate_and_sanitize_nutrition(bad_food, basis="per 100g", source="Test")
    assert sanitized["protein"] == 0.0
    assert len(res.warnings) > 0

    # Test 3: Macro sum exceeding 100g physical limit for 100g portion
    impossible_food = {
        "calories": 500.0,
        "protein": 60.0,
        "carbohydrates": 60.0,
        "fat": 30.0,  # 150g total macros in 100g
    }
    sanitized, res = validate_and_sanitize_nutrition(impossible_food, basis="per 100g", source="Test")
    assert res.is_valid is False
    assert res.verification_status == "suspicious"
    assert any("exceeds 100g" in err for err in res.errors)

    # Test 4: Sugar exceeding total carbohydrates
    bad_sugar = {
        "calories": 200.0,
        "protein": 5.0,
        "carbohydrates": 10.0,
        "sugar": 25.0,  # Impossible: sugar > carbs
        "fat": 5.0,
    }
    sanitized, res = validate_and_sanitize_nutrition(bad_sugar, basis="per 100g", source="Test")
    assert sanitized["sugar"] == 10.0  # Clamped to carbohydrates


def test_curated_local_food_database_staples():
    """Verify local database contains key Indian staples with verified nutritional data."""
    db = get_local_food_db()

    # Test Indian staples
    staples_to_check = [
        ("roti", "Roti (Whole Wheat Chapati)"),
        ("dal tadka", "Dal Tadka (Yellow Lentil Curry)"),
        ("paneer", "Paneer Tikka / Cottage Cheese Masala"),
        ("idli", "Idli (Steamed Rice & Lentil Cake)"),
        ("dosa", "Plain Dosa (Crispy Rice-Lentil Crepe)"),
        ("khichdi", "Khichdi (Rice and Moong Lentil Porridge)"),
        ("biryani", "Chicken Biryani"),
    ]

    for search_term, expected_name in staples_to_check:
        record = db.search_by_term(search_term)
        assert record is not None, f"Failed to find staple: {search_term}"
        assert record["canonical_name"] == expected_name
        assert record["calories"] > 0
        assert record["protein"] >= 0
        assert record["carbohydrates"] >= 0
        assert record["fat"] >= 0
        assert record["source"] != ""
        assert record["verification_status"] == "verified_standard"


@pytest.mark.asyncio
async def test_general_purpose_nutrition_lookup_non_20_foods():
    """Verify nutrition lookup succeeds for foods completely outside original 20 classes."""
    non_20_foods = ["roti", "dal tadka", "banana", "salmon", "almonds", "quinoa"]

    for food in non_20_foods:
        data = await get_nutrition_for_food(food)
        assert data is not None, f"Failed lookup for {food}"
        assert data.data_available is True
        assert data.food_name != ""
        assert data.calories is not None and data.calories > 0
        assert data.protein is not None and data.protein >= 0
        assert data.source != ""
        assert data.is_validated is True


@pytest.mark.asyncio
async def test_streaming_chat_endpoint_structure():
    """Verify /api/chat/stream returns valid Server-Sent Events (SSE)."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "message": "What nutrients are in 100g of almonds?",
            "history": []
        }
        response = await ac.post("/api/chat/stream", json=payload)
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")
        body = response.text
        assert "data: " in body


@pytest.mark.asyncio
async def test_nutrition_cache_hit():
    """Verify that repeated queries hit the in-memory TTL cache."""
    nutrition_cache.clear()

    # First fetch (populates cache)
    d1 = await get_nutrition_for_food("apple")
    assert d1 is not None

    stats_before = nutrition_cache.get_stats()

    # Second fetch (should hit cache)
    d2 = await get_nutrition_for_food("apple")
    assert d2 is not None

    stats_after = nutrition_cache.get_stats()
    assert stats_after["hits"] > stats_before["hits"]
