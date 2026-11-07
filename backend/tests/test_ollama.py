"""
NutriGuide AI - Ollama / Gemma 3 4B IT Integration Tests
Covers configuration, health checks, mocked unit tests, error handling,
and API endpoint integration.
"""
import pytest
from unittest.mock import MagicMock, patch
from httpx import AsyncClient, ASGITransport
import httpx

from app.main import app
from app.core.config import settings
from app.services.ollama_service import (
    check_ollama_health,
    is_ollama_configured,
    _build_nutrition_context,
    chat_with_context,
    classify_food_with_vision,
    explain_nutrition,
)
from app.api.chat import _detect_food_in_query


# ============================================================
# A. CONFIGURATION & HEALTH CHECKS
# ============================================================

def test_ollama_configuration():
    """Verify backend recognizes Ollama configuration."""
    assert is_ollama_configured() is True
    assert settings.ollama_model == "gemma3:4b"
    assert "11434" in settings.ollama_base_url


@pytest.mark.asyncio
async def test_ollama_health_check_running():
    """Verify check_ollama_health reports True when model is present."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "models": [{"name": "gemma3:4b"}, {"name": "llama3:latest"}]
    }

    with patch("httpx.AsyncClient.get", return_value=mock_resp):
        health = await check_ollama_health()
        assert health["available"] is True
        assert health["model"] == "gemma3:4b"


@pytest.mark.asyncio
async def test_ollama_health_check_offline():
    """Verify check_ollama_health reports False when server is offline."""
    with patch("httpx.AsyncClient.get", side_effect=httpx.ConnectError("Connection refused")):
        health = await check_ollama_health()
        assert health["available"] is False
        assert "not running" in health["error"].lower()


@pytest.mark.asyncio
async def test_ollama_health_check_model_missing():
    """Verify check_ollama_health reports False when gemma3:4b is not yet pulled."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "models": [{"name": "mistral:latest"}]
    }

    with patch("httpx.AsyncClient.get", return_value=mock_resp):
        health = await check_ollama_health()
        assert health["available"] is False
        assert "ollama pull gemma3:4b" in health["error"]


# ============================================================
# B. PROMPT & CONTEXT CONSTRUCTION
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


# ============================================================
# C. UNIT TESTS (Mocked Ollama Inference)
# ============================================================

@pytest.mark.asyncio
async def test_chat_with_context_mocked_success():
    """Verify chat returns correctly formatted answer and attributions with mocked Ollama."""
    mock_reply = "Fried rice contains 163 kcal and 5.2g protein per 100g based on USDA data."
    with patch("app.services.ollama_service._ollama_chat", return_value=mock_reply):
        res = await chat_with_context(
            user_message="macros of fried rice",
            food_context={"food_name": "Fried rice"},
        )
        assert res["warning"] is None
        assert "163 kcal" in res["answer"]
        assert res["evidence_used"] is True


@pytest.mark.asyncio
async def test_chat_with_context_mocked_offline():
    """Verify graceful handling when Ollama is offline."""
    with patch("app.services.ollama_service._ollama_chat", side_effect=httpx.ConnectError("Connection refused")):
        res = await chat_with_context("test query")
        assert "ollama serve" in res["answer"].lower()
        assert res["warning"] == "Ollama server not running"


@pytest.mark.asyncio
async def test_chat_with_context_mocked_timeout():
    """Verify graceful handling when Ollama request times out."""
    with patch("app.services.ollama_service._ollama_chat", side_effect=httpx.TimeoutException("Timed out")):
        res = await chat_with_context("test query")
        assert "took too long" in res["answer"].lower()
        assert res["warning"] == "Request timed out"


@pytest.mark.asyncio
async def test_explain_nutrition_wrapper():
    """Verify explain_nutrition generates a concise summary via chat_with_context."""
    mock_reply = "Apples are rich in fiber and vitamin C with 52 calories per 100g."
    with patch("app.services.ollama_service._ollama_chat", return_value=mock_reply):
        summary = await explain_nutrition("Apple", {"calories": 52, "fiber": 2.4})
        assert "Apples" in summary


# ============================================================
# D. ENDPOINT INTEGRATION TESTS
# ============================================================

@pytest.mark.asyncio
async def test_chat_endpoint_empty_message():
    """Verify endpoint rejects empty queries with HTTP 400."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.post("/api/chat", json={"message": "   "})
        assert r.status_code == 400


@pytest.mark.asyncio
async def test_chat_endpoint_schema_contract():
    """Verify endpoint response matches ChatResponse Pydantic schema with mocked Ollama."""
    mock_reply = "Protein supports muscle growth and tissue repair."
    with patch("app.services.ollama_service._ollama_chat", return_value=mock_reply):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            r = await ac.post("/api/chat", json={"message": "What is protein?"})
            assert r.status_code == 200
            data = r.json()
            assert "answer" in data
            assert "sources" in data
            assert isinstance(data["sources"], list)
            assert "evidence_used" in data
            assert isinstance(data["evidence_used"], bool)
            assert "Protein supports muscle" in data["answer"]


@pytest.mark.asyncio
async def test_compare_endpoint_with_ollama():
    """Verify comparison endpoint produces AI summary via Ollama."""
    mock_reply = "Pizza is higher in calories and sodium than salad, which provides more vitamins."
    with patch("app.services.ollama_service._ollama_chat", return_value=mock_reply):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            r = await ac.post("/api/compare", json={"food1": "Pizza", "food2": "Salad"})
            assert r.status_code == 200
            data = r.json()
            assert data["ai_summary"] is not None
            assert "Pizza is higher" in data["ai_summary"]
