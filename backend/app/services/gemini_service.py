"""
NutriGuide AI - Gemini AI Integration
"""
import logging
from typing import Optional, Dict, Any, List
import google.generativeai as genai
from app.core.config import settings
from app.schemas.food import ChatMessage

logger = logging.getLogger(__name__)

_model = None


def get_model():
    global _model
    if _model is None:
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is not configured")
        genai.configure(api_key=settings.gemini_api_key)
        _model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=(
                "You are NutriGuide AI, a helpful nutrition assistant. "
                "You MUST follow these rules strictly:\n"
                "1. Only use nutrition data explicitly provided in the context. Never invent values.\n"
                "2. Clearly state when data is missing or unavailable.\n"
                "3. Distinguish between verified data and general explanations.\n"
                "4. Do not make medical or dietary recommendations.\n"
                "5. Explain nutrition terminology in simple language.\n"
                "6. If uncertain, say so explicitly.\n"
                "7. Keep responses concise and focused."
            )
        )
    return _model


def _build_nutrition_context(food_context: Optional[Dict[str, Any]]) -> str:
    """Build a structured context string from food data for the LLM."""
    if not food_context:
        return ""

    lines = ["\n=== VERIFIED FOOD DATA (use this data only) ==="]

    if food_context.get("food_name"):
        lines.append(f"Food: {food_context['food_name']}")

    if food_context.get("classification"):
        clf = food_context["classification"]
        lines.append(f"Image Classification: {clf.get('display_name', '')} (confidence: {clf.get('confidence', 0)*100:.1f}%)")
        if not clf.get("is_confident"):
            lines.append("WARNING: Classification confidence is below threshold - user should verify.")

    if food_context.get("nutrition"):
        n = food_context["nutrition"]
        lines.append(f"\nNutrition Data (source: {n.get('source', 'USDA')}, basis: {n.get('basis', 'per 100g')}):")
        if n.get("calories") is not None:
            lines.append(f"  Calories: {n['calories']} kcal")
        if n.get("protein") is not None:
            lines.append(f"  Protein: {n['protein']} g")
        if n.get("carbohydrates") is not None:
            lines.append(f"  Carbohydrates: {n['carbohydrates']} g")
        if n.get("fat") is not None:
            lines.append(f"  Fat: {n['fat']} g")
        if n.get("sugar") is not None:
            lines.append(f"  Sugar: {n['sugar']} g")
        if n.get("fiber") is not None:
            lines.append(f"  Fiber: {n['fiber']} g")
        if n.get("sodium") is not None:
            lines.append(f"  Sodium: {n['sodium']} mg")
        if not n.get("data_available"):
            lines.append("  NOTE: Nutrition data not available for this food.")

    if food_context.get("product"):
        p = food_context["product"]
        lines.append(f"\nProduct Information (source: Open Food Facts):")
        if p.get("product_name"):
            lines.append(f"  Product: {p['product_name']}")
        if p.get("brands"):
            lines.append(f"  Brand: {p['brands']}")
        if p.get("ingredients_text"):
            lines.append(f"  Ingredients: {p['ingredients_text'][:500]}")
        if p.get("allergens"):
            lines.append(f"  Declared Allergens: {p['allergens']}")
        else:
            lines.append("  Allergens: Not declared in database (absence does NOT confirm allergen-free)")
        if p.get("missing_fields"):
            lines.append(f"  Missing data: {', '.join(p['missing_fields'])}")

    if food_context.get("rag_context"):
        lines.append(f"\nRetrieved Reference Information:\n{food_context['rag_context']}")

    lines.append("=" * 50)
    return "\n".join(lines)


async def chat_with_context(
    user_message: str,
    food_context: Optional[Dict[str, Any]] = None,
    history: Optional[List[ChatMessage]] = None,
) -> Dict[str, Any]:
    """Send a message to Gemini with food context and conversation history."""
    try:
        model = get_model()
    except ValueError as e:
        return {
            "answer": f"AI assistant is not configured. {str(e)}",
            "sources": [],
            "evidence_used": False,
            "warning": "GEMINI_API_KEY not set",
        }

    context_str = _build_nutrition_context(food_context)
    evidence_used = bool(context_str)

    # Build history for Gemini
    gemini_history = []
    if history:
        for msg in history[-6:]:  # Keep last 6 messages to stay within context
            role = "user" if msg.role == "user" else "model"
            gemini_history.append({"role": role, "parts": [msg.content]})

    # Compose the full prompt
    if context_str:
        full_prompt = f"{context_str}\n\nUser question: {user_message}"
    else:
        full_prompt = user_message

    sources = []
    if food_context:
        if food_context.get("nutrition"):
            sources.append(food_context["nutrition"].get("source", "USDA FoodData Central"))
        if food_context.get("product"):
            sources.append("Open Food Facts")
        if food_context.get("rag_context"):
            sources.append("NutriGuide Knowledge Base")

    try:
        chat = model.start_chat(history=gemini_history)
        response = await chat.send_message_async(full_prompt)
        answer = response.text
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        return {
            "answer": "I encountered an error while processing your request. Please try again.",
            "sources": [],
            "evidence_used": False,
            "warning": f"AI service error: {type(e).__name__}",
        }

    return {
        "answer": answer,
        "sources": sources,
        "evidence_used": evidence_used,
        "warning": None,
    }


async def explain_nutrition(food_name: str, nutrition_data: Dict[str, Any]) -> str:
    """Generate a simple explanation of nutrition data for a food."""
    result = await chat_with_context(
        user_message=f"Explain the nutritional content of {food_name} in simple, friendly language. Focus on what makes it nutritious or not, and any notable characteristics. Keep it under 150 words.",
        food_context={"food_name": food_name, "nutrition": nutrition_data},
    )
    return result["answer"]
