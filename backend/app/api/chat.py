"""NutriGuide AI - AI Chat Router with RAG"""
import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from app.services.gemini_service import chat_with_context
from app.rag.rag_service import get_rag_service
from app.schemas.food import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with the AI nutrition assistant.
    Uses RAG retrieval + verified food context to ground responses.
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    # Retrieve RAG context for the user's question
    rag_service = get_rag_service()
    rag_context = rag_service.get_context_string(request.message, k=3)

    # Merge RAG context into food_context
    food_context: Dict[str, Any] = dict(request.food_context) if request.food_context else {}
    if rag_context:
        food_context["rag_context"] = rag_context

    try:
        result = await chat_with_context(
            user_message=request.message,
            food_context=food_context if food_context else None,
            history=request.history,
        )
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail="AI assistant is temporarily unavailable.")

    sources = result.get("sources", [])
    if rag_context:
        sources.append("NutriGuide Knowledge Base")

    return ChatResponse(
        answer=result["answer"],
        sources=list(set(sources)),
        evidence_used=result.get("evidence_used", False),
        warning=result.get("warning"),
    )
