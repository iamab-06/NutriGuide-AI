"""
NutriGuide AI - Gemini Integration Tests
Covers configuration, mocked unit tests, error handling, and live API verification.
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.config import settings
from app.services.gemini_service import (
    is_gemini_configured,
    _build_nutrition_context,
    chat_with_context,
    explain_nutrition,
    MODEL_CANDIDATES,
)
from app.api.chat import _detect_food_in_query


# ============================================================
# A. CONFIGURATION TESTS
# ============================================================

def test_gemini_configuration_detection():
    """Verify backend recognizes whether GEMINI_API_KEY is configured without exposing it."""
    configured = is_gemini_configured()
    assert isinstance(configured, bool)
    assert configured is True, "Expected GEMINI_API_KEY to be configured in backend/.env"


def test_gemini_key_never_exposed_in_config():
    """Ensure string representation of settings does not expose raw key."""
    s_repr = repr(settings)
    assert settings.gemini_api_key not in s_repr or len(settings.gemini_api_key) == 0


def test_missing_key_behavior():
    """Verify that unconfigured key yields a clean, safe message without crashing."""
    with patch("app.services.gemini_service.is_gemini_configured", return_value=False):
        import asyncio
        res = asyncio.run(chat_with_context("Hello nutrition"))
        assert "AI assistant is not configured" in res["answer"]
        assert res["warning"] == "GEMINI_API_KEY not configured"
        assert res["evidence_used"] is False


# ============================================================
# B. UNIT TESTS (Mocked)
# ============================================================

def test_food_detection_in_query():
    """Verify food name entity detection in chat queries."""
    res1 = _detect_food_in_query("What are the macros of fried rice?")
    assert res1 is not None
    assert res1[0] == "fried_rice"
    assert res1[1] == "Fried Rice"

    res2 = _detect_food_in_query("Is cheese pizza healthy?")
    assert res2 is not None
    assert res2[0] == "pizza"

    res3 = _detect_food_in_query("What is the weather today?")
    assert res3 is None


def test_build_nutrition_context_complete():
    """Test structured prompt context construction with full verified evidence."""
    food_ctx = {
        "food_name": "Cheese Pizza",
        "nutrition": {
            "source": "USDA FoodData Central",
            "basis": "per 100g",
            "calories": 266.0,
            "protein": 10.5,
            "carbohydrates": 33.0,
            "fat": 10.0,
            "sugar": 3.6,
            "fiber": 2.3,
            "sodium": 598.0,
            "data_available": True,
        },
        "product": {
            "product_name": "Frozen Pizza",
            "brands": "BrandX",
            "ingredients_text": "Wheat flour, cheese, tomato sauce",
            "allergens": "milk, gluten",
            "missing_fields": [],
        },
        "rag_context": "[1] Fiber aids digestion.",
    }

    ctx = _build_nutrition_context(food_ctx)
    assert "=== VERIFIED FOOD DATA" in ctx
    assert "Cheese Pizza" in ctx
    assert "Calories: 266.0 kcal" in ctx
    assert "Protein: 10.5 g" in ctx
    assert "BrandX" in ctx
    assert "Declared Allergens: milk, gluten" in ctx
    assert "Fiber aids digestion" in ctx


def test_build_nutrition_context_empty():
    """Test context construction when no food context is supplied."""
    ctx = _build_nutrition_context(None)
    assert ctx == ""
    ctx_empty = _build_nutrition_context({})
    assert ctx_empty == ""


@pytest.mark.asyncio
async def test_chat_with_context_mocked_success():
    """[MOCKED UNIT TEST] Verify prompt passing and response formatting with mocked Gemini."""
    mock_chat = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "Fried rice contains 163 kcal and 5.2g protein per 100g based on USDA data."
    mock_chat.send_message.return_value = mock_response

    mock_model = MagicMock()
    mock_model.start_chat.return_value = mock_chat

    with patch("app.services.gemini_service.get_model", return_value=mock_model):
        with patch("app.services.gemini_service.is_gemini_configured", return_value=True):
            res = await chat_with_context(
                user_message="macros of fried rice",
                food_context={"food_name": "Fried rice"},
            )
            assert res["warning"] is None
            assert "163 kcal" in res["answer"]
            assert res["evidence_used"] is True


@pytest.mark.asyncio
async def test_chat_with_context_mocked_rate_limit():
    """[MOCKED UNIT TEST] Verify graceful handling of ResourceExhausted (rate limit)."""
    from google.api_core import exceptions as g_exc

    mock_chat = MagicMock()
    mock_chat.send_message.side_effect = g_exc.ResourceExhausted("429 Quota Exceeded")

    mock_model = MagicMock()
    mock_model.start_chat.return_value = mock_chat

    with patch("app.services.gemini_service.get_model", return_value=mock_model):
        with patch("app.services.gemini_service.is_gemini_configured", return_value=True):
            res = await chat_with_context("test query")
            assert "rate limit" in res["answer"].lower() or "quota" in res["answer"].lower()
            assert res["warning"] == "Provider rate limit / quota exceeded"


# ============================================================
# C. APPLICATION ENDPOINT INTEGRATION TESTS
# ============================================================

@pytest.mark.asyncio
async def test_chat_endpoint_empty_message():
    """Verify endpoint rejects empty queries with HTTP 400."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.post("/api/chat", json={"message": "   "})
        assert r.status_code == 400


@pytest.mark.asyncio
async def test_chat_endpoint_schema_contract():
    """Verify endpoint response matches ChatResponse Pydantic schema."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.post("/api/chat", json={"message": "What is protein?"})
        assert r.status_code == 200
        data = r.json()
        assert "answer" in data
        assert "sources" in data
        assert isinstance(data["sources"], list)
        assert "evidence_used" in data
        assert isinstance(data["evidence_used"], bool)


# ============================================================
# D. LIVE GEMINI API TEST (Real Provider Inference)
# ============================================================

@pytest.mark.asyncio
async def test_live_gemini_api_inference():
    """[LIVE API TEST] Send an actual non-sensitive test query to Gemini and verify live response."""
    if not is_gemini_configured():
        pytest.skip("GEMINI_API_KEY is not configured; skipping live provider test")

    res = await chat_with_context(
        user_message="In one short sentence, define what a calorie is.",
    )

    assert res["warning"] is None, f"Encountered warning: {res.get('warning')}"
    assert len(res["answer"]) > 10, "Expected non-empty response from live API"
    assert "energy" in res["answer"].lower() or "calorie" in res["answer"].lower() or "heat" in res["answer"].lower()
