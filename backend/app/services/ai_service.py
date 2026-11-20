"""
NutriGuide AI - Unified AI Service
Automatically routes to Gemini API (when GEMINI_API_KEY is set)
or Ollama/Gemma 3 4B IT (when running locally without an API key).

Usage: import this module instead of gemini_service or ollama_service directly.
  - Production (Railway): uses Gemini API  → all features work
  - Local development:    uses Ollama       → all features work
"""
import logging
from typing import Optional, Dict, Any, List

from app.core.config import settings
from app.schemas.food import ChatMessage

logger = logging.getLogger(__name__)


def _use_gemini() -> bool:
    """Return True if a valid Gemini API key is configured."""
    key = settings.gemini_api_key
    return bool(key and key.strip() and key not in ("", "your_gemini_api_key_here"))


# ---------------------------------------------------------------------------
# Public: chat_with_context
# Routes to Gemini or Ollama depending on environment.
# ---------------------------------------------------------------------------

async def chat_with_context(
    user_message: str,
    food_context: Optional[Dict[str, Any]] = None,
    history: Optional[List[ChatMessage]] = None,
) -> Dict[str, Any]:
    if _use_gemini():
        logger.debug("AI routing: Gemini API")
        from app.services.gemini_service import chat_with_context as _gemini_chat
        return await _gemini_chat(user_message, food_context, history)
    else:
        logger.debug("AI routing: Ollama (local)")
        from app.services.ollama_service import chat_with_context as _ollama_chat
        return await _ollama_chat(user_message, food_context, history)


# ---------------------------------------------------------------------------
# Public: stream_chat_with_context
# ---------------------------------------------------------------------------

async def stream_chat_with_context(
    user_message: str,
    food_context: Optional[Dict[str, Any]] = None,
    history: Optional[List[ChatMessage]] = None,
):
    """
    Async generator streaming tokens.
    Gemini does not support token streaming via the basic SDK, so we fall
    back to yielding the full answer as one token when using Gemini.
    """
    if _use_gemini():
        logger.debug("AI stream routing: Gemini API (single-chunk)")
        result = await chat_with_context(user_message, food_context, history)
        yield {"event": "meta", "sources": result.get("sources", []), "evidence_used": result.get("evidence_used", False)}
        yield {"event": "token", "token": result.get("answer", "")}
        yield {"event": "done"}
    else:
        logger.debug("AI stream routing: Ollama (streaming)")
        from app.services.ollama_service import stream_chat_with_context as _ollama_stream
        async for chunk in _ollama_stream(user_message, food_context, history):
            yield chunk


# ---------------------------------------------------------------------------
# Public: classify_food_with_vision
# ---------------------------------------------------------------------------

async def classify_food_with_vision(image_bytes: bytes) -> Dict[str, Any]:
    if _use_gemini():
        logger.debug("Vision routing: Gemini Vision API")
        from app.services.gemini_service import classify_food_with_gemini
        return await classify_food_with_gemini(image_bytes)
    else:
        logger.debug("Vision routing: Ollama multimodal")
        from app.services.ollama_service import classify_food_with_vision as _ollama_vision
        return await _ollama_vision(image_bytes)


# ---------------------------------------------------------------------------
# Public: explain_nutrition
# ---------------------------------------------------------------------------

async def explain_nutrition(food_name: str, nutrition_data: Dict[str, Any]) -> str:
    if _use_gemini():
        from app.services.gemini_service import explain_nutrition as _gemini_explain
        return await _gemini_explain(food_name, nutrition_data)
    else:
        from app.services.ollama_service import explain_nutrition as _ollama_explain
        return await _ollama_explain(food_name, nutrition_data)
