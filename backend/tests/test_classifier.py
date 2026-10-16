"""
Tests for food image classification and confidence thresholding
"""
import io
import pytest
from PIL import Image
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.services.classifier import FoodClassifier, CONFIDENCE_THRESHOLD


def create_test_image(format="JPEG", size=(224, 224), color=(255, 0, 0)) -> bytes:
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format=format)
    return buf.getvalue()


def test_classifier_predict_synthetic_image():
    classifier = FoodClassifier()
    img_bytes = create_test_image()
    result = classifier.predict(img_bytes)

    assert "predicted_class" in result
    assert "display_name" in result
    assert "confidence" in result
    assert "top_predictions" in result
    assert "is_confident" in result
    assert len(result["top_predictions"]) <= 5
    assert result["confidence_threshold"] == CONFIDENCE_THRESHOLD
    # Verify probabilities sum check or range
    assert 0.0 <= result["confidence"] <= 1.0


@pytest.mark.asyncio
async def test_analyze_endpoint_invalid_file_type():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/analyze",
            files={"file": ("test.txt", b"not an image", "text/plain")}
        )
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


@pytest.mark.asyncio
async def test_analyze_endpoint_valid_image():
    img_bytes = create_test_image()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/analyze",
            files={"file": ("food.jpg", img_bytes, "image/jpeg")}
        )
    assert response.status_code == 200
    data = response.json()
    assert "classification" in data
    assert "predicted_class" in data["classification"]
    assert "confidence" in data["classification"]
    assert "display_name" in data["classification"]
