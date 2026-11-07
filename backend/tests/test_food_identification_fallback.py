"""
NutriGuide AI - Tests for Food Identification, Uncertainty Handling, and Gemini Vision Fallback
Specifically verifies:
1. Correct local predictions above threshold (automatic nutrition retrieval).
2. Low-confidence predictions (< 70%, e.g., 43.9% samosa image) triggering Gemini Vision fallback.
3. Withholding definitive nutrition information until food identity is confirmed.
4. Gemini Vision identifying a samosa from an image.
5. Gemini Vision failure or unavailable credentials handling.
6. User correction of an incorrect prediction via the nutrition endpoint.
"""
import io
import glob
import pytest
from unittest.mock import patch, MagicMock
from PIL import Image
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.services.classifier import FoodClassifier, CONFIDENCE_THRESHOLD
from app.services.ollama_service import classify_food_with_vision, is_ollama_configured
from app.core.categories import SUPPORTED_CATEGORIES, CATEGORY_DISPLAY_NAMES


def create_sample_image(format="JPEG", size=(224, 224), color=(200, 150, 50)) -> bytes:
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format=format)
    return buf.getvalue()


def get_real_sample_image(category: str = "samosa", min_conf: float = 0.0) -> bytes:
    files = sorted(glob.glob(f"datasets/food20/val/{category}/*.jpg") or glob.glob(f"backend/datasets/food20/val/{category}/*.jpg"))
    if files:
        if min_conf > 0.0:
            clf = FoodClassifier()
            for fpath in files:
                with open(fpath, "rb") as f:
                    content = f.read()
                    if clf.predict(content)["confidence"] >= min_conf:
                        return content
        with open(files[0], "rb") as f:
            return f.read()
    return create_sample_image()


# ============================================================
# 1. CORRECT LOCAL PREDICTION (Above Threshold)
# ============================================================
@pytest.mark.asyncio
async def test_correct_local_prediction_above_threshold():
    """
    Verify that when local classifier is confident (>= 70%),
    definitive nutrition is automatically retrieved and Gemini Vision
    is NOT invoked unnecessarily.
    """
    img_bytes = get_real_sample_image("pizza", min_conf=CONFIDENCE_THRESHOLD)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/analyze",
            files={"file": ("pizza.jpg", img_bytes, "image/jpeg")}
        )

    assert response.status_code == 200
    data = response.json()

    clf = data["classification"]
    assert clf["predicted_class"] == "pizza"
    assert clf["is_confident"] is True
    assert clf["confidence"] >= CONFIDENCE_THRESHOLD
    assert data["requires_confirmation"] is False

    # Definitive nutrition must be retrieved for confident predictions
    assert data["nutrition"] is not None
    assert data["nutrition"]["data_available"] is True
    assert data["nutrition"]["calories"] is not None

    # Fallback should not run when local prediction is confident
    assert data["gemini_fallback"] is None


# ============================================================
# 2. LOW-CONFIDENCE PREDICTION (Triggers Gemini Vision Fallback)
# ============================================================
@pytest.mark.asyncio
async def test_low_confidence_prediction_triggers_gemini_fallback():
    """
    Verify that when local confidence is below threshold (< 70%, e.g. 43.9% Apple Pie),
    1. is_confident is False
    2. requires_confirmation is True
    3. Gemini Vision fallback is invoked
    4. Definitive nutrition is NOT retrieved automatically (nutrition is None)
    """
    mock_prediction = {
        "predicted_class": "apple_pie",
        "display_name": "Apple Pie",
        "confidence": 0.439,
        "top_predictions": [
            {"class": "apple_pie", "display_name": "Apple Pie", "confidence": 0.439, "confidence_pct": "43.9%"},
            {"class": "samosa", "display_name": "Samosa", "confidence": 0.385, "confidence_pct": "38.5%"},
            {"class": "spring_rolls", "display_name": "Spring Rolls", "confidence": 0.082, "confidence_pct": "8.2%"},
        ],
        "is_confident": False,
        "confidence_threshold": CONFIDENCE_THRESHOLD,
        "model_version": "MobileNetV3-NutriGuide-v1",
        "supported_categories": list(CATEGORY_DISPLAY_NAMES.values()),
    }

    mock_vision = {
        "available": True,
        "suggested_food": "Samosa",
        "category_match": "samosa",
        "confidence": "High",
        "explanation": "Observed golden-brown triangular fried pastry filled with spiced vegetables.",
        "source": "Gemma 3 4B IT (Ollama)",
        "error": None,
    }

    img_bytes = create_sample_image()

    with patch("app.api.analyze.get_classifier") as mock_get_clf:
        mock_clf_instance = MagicMock()
        mock_clf_instance.predict.return_value = mock_prediction
        mock_get_clf.return_value = mock_clf_instance

        with patch("app.api.analyze.classify_food_with_vision", return_value=mock_vision):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.post(
                    "/api/analyze",
                    files={"file": ("samosa.jpg", img_bytes, "image/jpeg")}
                )

    assert response.status_code == 200
    data = response.json()

    # Must be flagged as uncertain
    assert data["classification"]["is_confident"] is False
    assert data["requires_confirmation"] is True

    # CRITICAL: Definitive nutrition MUST be withheld for unconfirmed prediction
    assert data["nutrition"] is None

    # Vision fallback must be returned
    assert data["gemini_fallback"] is not None
    assert data["gemini_fallback"]["available"] is True
    assert data["gemini_fallback"]["suggested_food"] == "Samosa"
    assert data["gemini_fallback"]["category_match"] == "samosa"
    assert "Samosa" in data["message"]


# ============================================================
# 3. GEMMA 3 / OLLAMA VISION IDENTIFYING A SAMOSA
# ============================================================
@pytest.mark.asyncio
async def test_ollama_vision_identifying_samosa():
    """
    Verify that classify_food_with_vision parses and identifies a Samosa correctly.
    """
    mock_llm_json = '''```json
{
  "food_name": "Samosa",
  "category_match": "samosa",
  "confidence": "High",
  "explanation": "Triangular shaped crisp pastry with fried crust, characteristic of South Asian samosas."
}
```'''

    img_bytes = create_sample_image()

    with patch("app.services.ollama_service._ollama_chat", return_value=mock_llm_json):
        res = await classify_food_with_vision(img_bytes)

    assert res["available"] is True
    assert res["suggested_food"] == "Samosa"
    assert res["category_match"] == "samosa"
    assert res["confidence"] == "High"
    assert "Triangular" in res["explanation"]
    assert "Ollama" in res["source"]


# ============================================================
# 4. VISION FAILURE OR OLLAMA UNAVAILABLE HANDLING
# ============================================================
@pytest.mark.asyncio
async def test_vision_failure_or_ollama_unavailable():
    """
    Verify graceful behavior when Ollama server is offline or fails.
    The application must still return the local prediction, set nutrition=None,
    and prompt the user without crashing.
    """
    import httpx
    img_bytes = create_sample_image()

    # Case A: Ollama server not reachable (httpx.ConnectError)
    with patch("app.services.ollama_service._ollama_chat", side_effect=httpx.ConnectError("Connection refused")):
        res = await classify_food_with_vision(img_bytes)
        assert res["available"] is False
        assert "not running" in res["error"].lower()

    # Case B: Low-confidence image when vision fallback is unavailable
    mock_prediction = {
        "predicted_class": "apple_pie",
        "display_name": "Apple Pie",
        "confidence": 0.439,
        "top_predictions": [
            {"class": "apple_pie", "display_name": "Apple Pie", "confidence": 0.439, "confidence_pct": "43.9%"},
            {"class": "samosa", "display_name": "Samosa", "confidence": 0.385, "confidence_pct": "38.5%"},
        ],
        "is_confident": False,
        "confidence_threshold": CONFIDENCE_THRESHOLD,
        "model_version": "MobileNetV3-NutriGuide-v1",
        "supported_categories": list(CATEGORY_DISPLAY_NAMES.values()),
    }

    with patch("app.api.analyze.get_classifier") as mock_get_clf:
        mock_clf_instance = MagicMock()
        mock_clf_instance.predict.return_value = mock_prediction
        mock_get_clf.return_value = mock_clf_instance

        with patch("app.api.analyze.classify_food_with_vision", return_value={"available": False, "error": "Ollama server is not running", "source": "Gemma 3 4B IT (Ollama)"}):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.post(
                    "/api/analyze",
                    files={"file": ("samosa.jpg", img_bytes, "image/jpeg")}
                )

    assert response.status_code == 200
    data = response.json()
    assert data["classification"]["is_confident"] is False
    assert data["requires_confirmation"] is True
    assert data["nutrition"] is None
    assert data["gemini_fallback"]["available"] is False


# ============================================================
# 5. INCORRECT BUT ABOVE-THRESHOLD PREDICTION HANDLING
# ============================================================
@pytest.mark.asyncio
async def test_incorrect_above_threshold_prediction_structure():
    """
    Verify that even if a local model incorrectly predicts a class with high confidence
    (e.g., Apple Pie at 72%), the response includes the top alternative predictions
    and supported categories so the user can easily select the correct food.
    """
    mock_prediction = {
        "predicted_class": "apple_pie",
        "display_name": "Apple Pie",
        "confidence": 0.72,
        "top_predictions": [
            {"class": "apple_pie", "display_name": "Apple Pie", "confidence": 0.72, "confidence_pct": "72.0%"},
            {"class": "samosa", "display_name": "Samosa", "confidence": 0.20, "confidence_pct": "20.0%"},
            {"class": "spring_rolls", "display_name": "Spring Rolls", "confidence": 0.05, "confidence_pct": "5.0%"},
        ],
        "is_confident": True,
        "confidence_threshold": CONFIDENCE_THRESHOLD,
        "model_version": "MobileNetV3-NutriGuide-v1",
        "supported_categories": list(CATEGORY_DISPLAY_NAMES.values()),
    }

    img_bytes = create_sample_image()

    with patch("app.api.analyze.get_classifier") as mock_get_clf:
        mock_clf_instance = MagicMock()
        mock_clf_instance.predict.return_value = mock_prediction
        mock_get_clf.return_value = mock_clf_instance

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post(
                "/api/analyze",
                files={"file": ("food.jpg", img_bytes, "image/jpeg")}
            )

    assert response.status_code == 200
    data = response.json()
    top_preds = data["classification"]["top_predictions"]
    classes = [p["class"] for p in top_preds]
    assert "samosa" in classes, "Samosa must be present in top alternatives for user correction"


# ============================================================
# 6. USER CORRECTION FLOW (Retrieving Nutrition for Confirmed Food)
# ============================================================
@pytest.mark.asyncio
async def test_user_correction_flow():
    """
    Verify the user correction workflow:
    When a user rejects an incorrect prediction (e.g., Apple Pie) and selects 'Samosa',
    the frontend calls /api/nutrition/Samosa?category_key=samosa.
    Verify that definitive USDA nutrition for Samosa is retrieved.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/nutrition/Samosa?category_key=samosa")

    assert response.status_code == 200
    nutrition = response.json()
    assert nutrition["data_available"] is True
    assert "samosa" in nutrition["food_name"].lower()
    assert nutrition["basis"] == "per 100g"
    assert nutrition["calories"] is not None
    assert nutrition["carbohydrates"] is not None
    assert nutrition["protein"] is not None
    assert nutrition["fat"] is not None


# ============================================================
# 7. NON-FOOD REJECTION GUARDRAIL
# ============================================================
@pytest.mark.asyncio
async def test_non_food_rejection_guardrail():
    """
    Verify that when an image is classified as non-food (e.g. perfume, person, gadget),
    the guardrail marks is_food=False, withholds nutrition, and avoids confirmation prompts.
    """
    mock_prediction = {
        "predicted_class": "macarons",
        "display_name": "Macarons",
        "confidence": 0.133,
        "top_predictions": [{"class": "macarons", "display_name": "Macarons", "confidence": 0.133, "confidence_pct": "13.3%"}],
        "is_confident": False,
        "confidence_threshold": CONFIDENCE_THRESHOLD,
        "model_version": "MobileNetV3-NutriGuide-v1",
        "supported_categories": SUPPORTED_CATEGORIES,
    }

    mock_vision_non_food = {
        "available": True,
        "is_food": False,
        "suggested_food": "Ajmal Ascend Perfume - 100 ml",
        "category_match": None,
        "confidence": "High",
        "explanation": "The image displays a bottle of perfume, not an edible food item.",
        "source": "Gemma 3 4B IT (Ollama)",
    }

    img_bytes = create_sample_image()

    with patch("app.api.analyze.get_classifier") as mock_get_clf, \
         patch("app.api.analyze.classify_food_with_vision", return_value=mock_vision_non_food):
        mock_clf_instance = MagicMock()
        mock_clf_instance.predict.return_value = mock_prediction
        mock_get_clf.return_value = mock_clf_instance

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post(
                "/api/analyze",
                files={"file": ("perfume.jpg", img_bytes, "image/jpeg")}
            )

    assert response.status_code == 200
    data = response.json()
    assert data["is_food"] is False
    assert data["nutrition"] is None
    assert data["requires_confirmation"] is False
    assert "Non-food item detected" in data["message"]
    assert data["gemini_fallback"]["is_food"] is False
