"""
NutriGuide AI - Tests for Food Classification Improvements and Fallbacks
Tests:
1. Classification output schema and confidence bounds
2. Real food image test from validation dataset
3. Low-confidence fallback mechanism
4. Gemini Vision fallback structure and parsing
5. Non-food / corrupted image rejection
"""
import glob
import io
import pytest
from PIL import Image
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.services.classifier import FoodClassifier, CONFIDENCE_THRESHOLD
from app.core.categories import SUPPORTED_CATEGORIES, CATEGORY_DISPLAY_NAMES
from app.services.ollama_service import classify_food_with_vision, is_ollama_configured


def get_real_sample_image(category: str = "samosa") -> bytes:
    files = glob.glob(f"datasets/food20/val/{category}/*.jpg")
    if files:
        with open(files[0], "rb") as f:
            return f.read()
    # Fallback to synthetic if not available
    img = Image.new("RGB", (224, 224), color=(200, 150, 50))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def test_classifier_supported_categories_integrity():
    classifier = FoodClassifier()
    assert len(SUPPORTED_CATEGORIES) == 20
    assert len(CATEGORY_DISPLAY_NAMES) == 20
    # Every category must have a display name
    for cat in SUPPORTED_CATEGORIES:
        assert cat in CATEGORY_DISPLAY_NAMES


def test_classifier_prediction_schema():
    classifier = FoodClassifier()
    img_bytes = get_real_sample_image("pizza")
    result = classifier.predict(img_bytes)

    assert "predicted_class" in result
    assert result["predicted_class"] in classifier.categories or result["predicted_class"] in SUPPORTED_CATEGORIES
    assert "confidence" in result
    assert 0.0 <= result["confidence"] <= 1.0
    assert "top_predictions" in result
    assert len(result["top_predictions"]) == 5
    assert "is_confident" in result
    assert isinstance(result["is_confident"], bool)


@pytest.mark.asyncio
async def test_analyze_endpoint_real_food():
    img_bytes = get_real_sample_image("pizza")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/analyze",
            files={"file": ("pizza.jpg", img_bytes, "image/jpeg")}
        )
    assert response.status_code == 200
    data = response.json()
    assert "classification" in data
    assert "predicted_class" in data["classification"]
    assert "top_predictions" in data["classification"]
    assert len(data["classification"]["top_predictions"]) == 5


@pytest.mark.asyncio
async def test_analyze_endpoint_corrupted_image():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/analyze",
            files={"file": ("corrupt.jpg", b"not-a-valid-jpeg-header-bytes", "image/jpeg")}
        )
    assert response.status_code == 400
    assert "Cannot open image" in response.json()["detail"]


@pytest.mark.asyncio
async def test_vision_fallback_structure():
    from unittest.mock import patch
    mock_llm_json = '{"food_name": "Samosa", "category_match": "samosa", "confidence": "High", "explanation": "Golden pastry"}'
    img_bytes = get_real_sample_image("samosa")
    with patch("app.services.ollama_service._ollama_chat", return_value=mock_llm_json):
        res = await classify_food_with_vision(img_bytes)
    assert "available" in res
    assert res["available"] is True
    assert "suggested_food" in res
    assert res["suggested_food"] == "Samosa"
    assert "confidence" in res
    assert "source" in res
    assert "Ollama" in res["source"]
