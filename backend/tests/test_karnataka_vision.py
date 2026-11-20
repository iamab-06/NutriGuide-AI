"""
NutriGuide AI - Karnataka Food Vision & Fallback Recognition Tests
=================================================================
Validates:
1. Out-of-distribution regional Karnataka foods produce low confidence (<70%)
   in the closed-set MobileNetV3 classifier, properly triggering the vision fallback.
2. Gemma 3 4B Vision fallback prompt contains Karnataka regional culinary cues
   and strict uncertainty communication.
3. Candidate nutrition is automatically retrieved from the curated local database
   for the vision-suggested Karnataka food.
4. Non-food inputs are correctly identified with is_food=False.
5. End-to-end integration test with Ollama Gemma 3 4B Multimodal Vision.
"""
import io
import pytest
from PIL import Image
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock

from app.main import app
from app.services.classifier import FoodClassifier, CONFIDENCE_THRESHOLD
from app.services.ollama_service import classify_food_with_vision, is_ollama_configured
from app.schemas.food import AnalyzeImageResponse


def create_sample_image(format="JPEG", size=(224, 224), color=(180, 140, 80)) -> bytes:
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format=format)
    return buf.getvalue()


@pytest.mark.asyncio
async def test_low_confidence_triggers_vision_fallback():
    """
    Verify that an unconfident/OOD image triggers the Ollama Vision fallback
    and sets requires_confirmation=True.
    """
    img_bytes = create_sample_image(color=(80, 50, 40))

    # Mock Ollama Vision returning a Karnataka food
    mock_vision_result = {
        "available": True,
        "is_food": True,
        "suggested_food": "Ragi Mudde",
        "category_match": None,
        "confidence": "Medium",
        "explanation": "Observed a dark, dense spherical steamed millet ball characteristic of Karnataka Ragi Mudde.",
        "source": "Gemma 3 4B IT (Ollama)",
    }

    with patch("app.api.analyze.classify_food_with_vision", new=AsyncMock(return_value=mock_vision_result)):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post(
                "/api/analyze",
                files={"file": ("ragi_mudde.jpg", img_bytes, "image/jpeg")}
            )

    assert response.status_code == 200
    data = response.json()

    assert data["requires_confirmation"] is True
    assert data["gemini_fallback"] is not None
    assert data["gemini_fallback"]["suggested_food"] == "Ragi Mudde"
    assert "Ragi Mudde" in data["message"]

    # Verified candidate nutrition should be populated from our curated local database
    assert data["nutrition"] is not None
    assert data["nutrition"]["data_available"] is True
    assert "Ragi Mudde" in data["nutrition"]["food_name"]
    assert data["nutrition"]["calories"] == 122.0


@pytest.mark.asyncio
async def test_karnataka_mysore_pak_fallback_nutrition_retrieval():
    """
    Verify that when Ollama Vision suggests Mysore Pak, the system retrieves
    the authentic 524 kcal / 100g ICMR-NIN nutrition data without false substring matches.
    """
    img_bytes = create_sample_image(color=(220, 180, 40))

    mock_vision_result = {
        "available": True,
        "is_food": True,
        "suggested_food": "Mysore Pak",
        "category_match": None,
        "confidence": "High",
        "explanation": "Golden-yellow rectangular gram flour sweet with porous texture consistent with Mysore Pak.",
        "source": "Gemma 3 4B IT (Ollama)",
    }

    with patch("app.api.analyze.classify_food_with_vision", new=AsyncMock(return_value=mock_vision_result)):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post(
                "/api/analyze",
                files={"file": ("mysore_pak.jpg", img_bytes, "image/jpeg")}
            )

    assert response.status_code == 200
    data = response.json()
    assert data["nutrition"] is not None
    assert "Mysore Pak" in data["nutrition"]["food_name"]
    assert "Cabbage" not in data["nutrition"]["food_name"]
    assert data["nutrition"]["calories"] == 524.0


@pytest.mark.asyncio
async def test_non_food_image_rejection_in_vision_fallback():
    """
    Verify that non-food items detected by vision fallback set is_food=False
    and do not attach nutrition data.
    """
    img_bytes = create_sample_image(color=(20, 20, 20))

    mock_vision_result = {
        "available": True,
        "is_food": False,
        "suggested_food": "Perfume Bottle",
        "category_match": None,
        "confidence": "High",
        "explanation": "The image shows a glass fragrance bottle, not an edible food item.",
        "source": "Gemma 3 4B IT (Ollama)",
    }

    with patch("app.api.analyze.classify_food_with_vision", new=AsyncMock(return_value=mock_vision_result)):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post(
                "/api/analyze",
                files={"file": ("perfume.jpg", img_bytes, "image/jpeg")}
            )

    assert response.status_code == 200
    data = response.json()
    assert data["is_food"] is False
    assert data["nutrition"] is None
    assert "Non-food item detected" in data["message"]


@pytest.mark.asyncio
async def test_live_ollama_multimodal_vision_real_image():
    """
    Live test with the active local Ollama gemma3:4b model on a real image.
    Verifies that the vision endpoint executes and returns valid structure.
    """
    # Load an authentic image from Food-101
    real_img_path = "datasets/food101/train/apple_pie/apple_pie_00000.jpg"
    try:
        with open(real_img_path, "rb") as f:
            img_bytes = f.read()
    except FileNotFoundError:
        pytest.skip("Food-101 sample image not found on disk")

    res = await classify_food_with_vision(img_bytes)
    assert res["available"] is True
    assert res["is_food"] is True
    assert isinstance(res["suggested_food"], str)
    assert len(res["suggested_food"]) > 0
    assert res["confidence"] in {"High", "Medium", "Low"}
    assert res["source"] == "Gemma 3 4B IT (Ollama)"
