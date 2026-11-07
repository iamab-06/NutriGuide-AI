"""
NutriGuide AI - Gemini AI Integration
Provides generative nutrition explanations, evidence-grounded chat,
and dietary concept analysis using Google Gemini.
"""
import io
import json
import logging
import asyncio
from typing import Optional, Dict, Any, List
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from PIL import Image, UnidentifiedImageError

from app.core.config import settings
from app.core.categories import SUPPORTED_CATEGORIES, CATEGORY_DISPLAY_NAMES
from app.schemas.food import ChatMessage

logger = logging.getLogger(__name__)

# Supported model candidates in order of preference
MODEL_CANDIDATES = [
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-flash-latest",
    "gemini-3.8-flash",
]

# Strict system instruction to eliminate hallucinations and preserve evidence integrity
SYSTEM_INSTRUCTION = (
    "You are NutriGuide AI, an authoritative nutrition and dietary assistant developed for "
    "an academic project at Siddaganga Institute of Technology.\n"
    "Your mission is to provide clear, helpful, evidence-grounded nutritional explanations.\n\n"
    "RULES YOU MUST STRICTLY FOLLOW:\n"
    "1. Evidence Grounding: When verified nutrition or packaged product data is provided in the prompt, "
    "you MUST base your factual claims on those exact numbers. Never fabricate or guess calorie counts, "
    "macronutrient ratios, vitamins, or ingredients.\n"
    "2. Transparent Missing Data: If specific nutrition, ingredient, or allergen data is absent or unavailable, "
    "explicitly inform the user rather than inventing numbers.\n"
    "3. Distinguish Specific vs General: Clearly distinguish between verified food-specific records "
    "(such as USDA FoodData Central per 100g) and general nutritional science concepts.\n"
    "4. Units & Measurements: Always preserve precise units (kcal, grams, milligrams) and state the measurement basis (e.g., per 100g).\n"
    "5. Allergens & Safety: Packaged product data is sourced from Open Food Facts. The absence of declared allergens "
    "does NOT confirm that a food is allergen-free; always remind users to inspect the physical packaging.\n"
    "6. Non-Medical Disclaimer: Do not prescribe medical diets, diagnose health conditions, or offer clinical advice. "
    "Provide objective educational information only.\n"
    "7. Accessible Explanations: Explain nutritional terms (e.g., macronutrients, dietary fiber, sodium, saturated fats) "
    "in simple, friendly, easy-to-understand language.\n"
    "8. Uncertainty: If an image classification or data point is noted as low-confidence or uncertain, communicate that clearly."
)

_cached_model = None
_cached_model_name: Optional[str] = None


def is_gemini_configured() -> bool:
    """Check whether a Gemini API key is configured without exposing its value."""
    key = settings.gemini_api_key
    return bool(key and key.strip() and key != "your_gemini_api_key_here")


def get_model(force_refresh: bool = False, model_name: Optional[str] = None):
    """
    Get or initialize the Gemini GenerativeModel instance.
    Falls back gracefully across candidate models if one is deprecated or unavailable.
    """
    global _cached_model, _cached_model_name

    if not is_gemini_configured():
        raise ValueError("GEMINI_API_KEY is not configured")

    if _cached_model is not None and not force_refresh and (model_name is None or model_name == _cached_model_name):
        return _cached_model

    genai.configure(api_key=settings.gemini_api_key.strip())

    candidates = [model_name] if model_name else MODEL_CANDIDATES
    last_err = None

    for candidate in candidates:
        try:
            m = genai.GenerativeModel(
                model_name=candidate,
                system_instruction=SYSTEM_INSTRUCTION,
            )
            _cached_model = m
            _cached_model_name = candidate
            logger.info(f"Initialized Gemini model: {candidate}")
            return _cached_model
        except Exception as e:
            logger.warning(f"Could not initialize candidate model '{candidate}': {e}")
            last_err = e

    raise RuntimeError(f"Unable to initialize any Gemini model candidate: {last_err}")


def _build_nutrition_context(food_context: Optional[Dict[str, Any]]) -> str:
    """Build a structured evidence string from food data for LLM prompt injection."""
    if not food_context:
        return ""

    lines = ["\n=== VERIFIED FOOD DATA (ground truth evidence) ==="]

    if food_context.get("food_name"):
        lines.append(f"Food Item: {food_context['food_name']}")

    if food_context.get("classification"):
        clf = food_context["classification"]
        disp = clf.get("display_name", "")
        conf = clf.get("confidence", 0) * 100
        lines.append(f"Computer Vision Classification: {disp} (Confidence: {conf:.1f}%)")
        if not clf.get("is_confident"):
            lines.append("Note: Classification confidence is below threshold (40%). User verification advised.")

    if food_context.get("nutrition"):
        n = food_context["nutrition"]
        source = n.get("source", "USDA FoodData Central")
        basis = n.get("basis", "per 100g")
        lines.append(f"\nNutritional Content ({source}, basis: {basis}):")
        if n.get("calories") is not None:
            lines.append(f"  - Calories: {n['calories']} kcal")
        if n.get("protein") is not None:
            lines.append(f"  - Protein: {n['protein']} g")
        if n.get("carbohydrates") is not None:
            lines.append(f"  - Carbohydrates: {n['carbohydrates']} g")
        if n.get("fat") is not None:
            lines.append(f"  - Total Fat: {n['fat']} g")
        if n.get("sugar") is not None:
            lines.append(f"  - Sugar: {n['sugar']} g")
        if n.get("fiber") is not None:
            lines.append(f"  - Dietary Fiber: {n['fiber']} g")
        if n.get("sodium") is not None:
            lines.append(f"  - Sodium: {n['sodium']} mg")
        if n.get("cholesterol") is not None:
            lines.append(f"  - Cholesterol: {n['cholesterol']} mg")
        if n.get("saturated_fat") is not None:
            lines.append(f"  - Saturated Fat: {n['saturated_fat']} g")
        if not n.get("data_available", True):
            lines.append("  - Status: Detailed nutrition data unavailable in database.")

    if food_context.get("product"):
        p = food_context["product"]
        lines.append(f"\nPackaged Product Details (Open Food Facts):")
        if p.get("product_name"):
            lines.append(f"  - Product Name: {p['product_name']}")
        if p.get("brands"):
            lines.append(f"  - Brand: {p['brands']}")
        if p.get("ingredients_text"):
            lines.append(f"  - Ingredients: {p['ingredients_text'][:500]}")
        if p.get("allergens"):
            lines.append(f"  - Declared Allergens: {p['allergens']}")
        else:
            lines.append("  - Declared Allergens: None declared in database (absence does NOT confirm allergen-free)")
        if p.get("missing_fields"):
            lines.append(f"  - Missing Fields: {', '.join(p['missing_fields'])}")

    if food_context.get("rag_context"):
        lines.append(f"\nRetrieved Knowledge Base Principles:\n{food_context['rag_context']}")

    lines.append("=" * 50)
    return "\n".join(lines)


async def chat_with_context(
    user_message: str,
    food_context: Optional[Dict[str, Any]] = None,
    history: Optional[List[ChatMessage]] = None,
) -> Dict[str, Any]:
    """
    Send a message to Gemini with optional food context and conversation history.
    Returns structured answer, sources, evidence status, and any warnings.
    """
    if not is_gemini_configured():
        return {
            "answer": (
                "AI assistant is not configured. GEMINI_API_KEY is not configured in backend/.env. "
                "Please add a valid Google Gemini API key to enable AI responses."
            ),
            "sources": [],
            "evidence_used": False,
            "warning": "GEMINI_API_KEY not configured",
        }

    try:
        model = get_model()
    except Exception as e:
        logger.error(f"Failed to initialize Gemini model: {e}")
        return {
            "answer": "The AI assistant could not be initialized. Please check backend configuration.",
            "sources": [],
            "evidence_used": False,
            "warning": "Model initialization failed",
        }

    context_str = _build_nutrition_context(food_context)
    evidence_used = bool(context_str)

    # Format conversation history
    gemini_history = []
    if history:
        for msg in history[-6:]:
            role = "user" if msg.role == "user" else "model"
            gemini_history.append({"role": role, "parts": [msg.content]})

    # Compose final prompt
    if context_str:
        full_prompt = (
            f"{context_str}\n\n"
            f"User Question: {user_message}\n\n"
            "Respond accurately using the verified data above. Delineate between specific verified figures "
            "and general nutritional principles."
        )
    else:
        full_prompt = user_message

    # Collect source attributions
    sources: List[str] = []
    if food_context:
        if food_context.get("nutrition"):
            sources.append(food_context["nutrition"].get("source", "USDA FoodData Central"))
        if food_context.get("product"):
            sources.append("Open Food Facts")
        if food_context.get("rag_context"):
            sources.append("NutriGuide Knowledge Base")

    # Send request with candidate loop and robust error handling
    last_warning = None
    for candidate_name in MODEL_CANDIDATES:
        try:
            current_model = get_model(force_refresh=False, model_name=candidate_name)
            chat = current_model.start_chat(history=gemini_history)
            response = await asyncio.wait_for(
                asyncio.to_thread(chat.send_message, full_prompt),
                timeout=45.0
            )

            if response and response.text:
                return {
                    "answer": response.text.strip(),
                    "sources": sources,
                    "evidence_used": evidence_used,
                    "warning": None,
                }
        except (google_exceptions.ResourceExhausted, google_exceptions.NotFound, google_exceptions.InvalidArgument) as e:
            logger.warning(f"Candidate model '{candidate_name}' returned {type(e).__name__}. Trying next candidate...")
            last_warning = "Provider rate limit / quota exceeded"
            continue
        except (google_exceptions.PermissionDenied, google_exceptions.Unauthenticated) as e:
            logger.error(f"Gemini API authentication failed: {e}")
            return {
                "answer": "Gemini API key is invalid or lacks required permissions. Please verify credentials in backend/.env.",
                "sources": sources,
                "evidence_used": evidence_used,
                "warning": "Authentication error",
            }
        except asyncio.TimeoutError:
            logger.error(f"Gemini API request timed out on {candidate_name}")
            last_warning = "Request timed out"
            continue
        except Exception as e:
            logger.error(f"Unexpected Gemini API error on {candidate_name}: {type(e).__name__}: {e}")
            last_warning = f"AI service error: {type(e).__name__}"
            continue

    return {
        "answer": "The Gemini API quota or rate limit has been reached across available models. Please wait a moment and try again.",
        "sources": sources,
        "evidence_used": evidence_used,
        "warning": last_warning or "Provider rate limit / quota exceeded",
    }


async def explain_nutrition(food_name: str, nutrition_data: Dict[str, Any]) -> str:
    """Generate a concise, evidence-grounded nutritional explanation for a food item."""
    prompt = (
        f"Explain the nutritional profile of {food_name} in simple, friendly, easy-to-understand language. "
        "Highlight the primary macronutrients, calorie density, and any dietary considerations. Keep it under 150 words."
    )
    result = await chat_with_context(
        user_message=prompt,
        food_context={"food_name": food_name, "nutrition": nutrition_data},
    )
    return result["answer"]


async def classify_food_with_gemini(image_bytes: bytes) -> Dict[str, Any]:
    """
    Multimodal food classification using Google Gemini Vision as a fallback
    when local MobileNetV3 confidence is low (< 40%).
    
    Identifies the food item, matches against supported categories if applicable,
    and returns structured visual explanations.
    """
    if not is_gemini_configured():
        return {
            "available": False,
            "error": "Gemini API key is not configured.",
            "source": "Google Gemini Vision",
        }

    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception as e:
        return {
            "available": False,
            "error": f"Invalid image format: {e}",
            "source": "Google Gemini Vision",
        }

    categories_list = ", ".join(SUPPORTED_CATEGORIES)
    prompt = (
        "You are an expert food recognition system.\n"
        f"NutriGuide AI specifically tracks these 20 standard categories: [{categories_list}].\n\n"
        "Analyze the provided image and:\n"
        "1. Identify the specific food or dish shown.\n"
        "2. If it corresponds to one of the 20 categories above, specify that exact snake_case name in 'category_match'.\n"
        "   If it is a dish not in those 20, set 'category_match' to null.\n"
        "3. State your confidence as 'High', 'Medium', or 'Low'.\n"
        "4. Provide a clear 1-2 sentence description explaining what visual characteristics you observe.\n\n"
        "Respond ONLY with valid JSON in this exact structure:\n"
        "{\n"
        '  "food_name": "Name of food",\n'
        '  "category_match": "category_key_or_null",\n'
        '  "confidence": "High",\n'
        '  "explanation": "Clear explanation of visual evidence"\n'
        "}"
    )

    genai.configure(api_key=settings.gemini_api_key.strip())

    for candidate_name in MODEL_CANDIDATES:
        try:
            model = genai.GenerativeModel(candidate_name)
            response = await asyncio.wait_for(
                asyncio.to_thread(model.generate_content, [prompt, image]),
                timeout=45.0
            )
            text = response.text.strip()

            # Clean possible markdown fencing or outer wrappers
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            elif "{" in text and "}" in text:
                text = text[text.find("{"):text.rfind("}") + 1].strip()

            data = json.loads(text)
            cat_match = data.get("category_match")
            if cat_match and cat_match not in SUPPORTED_CATEGORIES:
                cat_match = None

            return {
                "available": True,
                "suggested_food": data.get("food_name"),
                "category_match": cat_match,
                "confidence": data.get("confidence", "Medium"),
                "explanation": data.get("explanation", ""),
                "source": "Google Gemini Vision",
            }
        except asyncio.TimeoutError:
            logger.warning(f"Gemini vision timed out on {candidate_name}. Trying next...")
            continue
        except (google_exceptions.ResourceExhausted, google_exceptions.NotFound) as e:
            logger.warning(f"Gemini vision error on {candidate_name}: {e}. Trying next...")
            continue
        except Exception as e:
            logger.warning(f"Gemini vision exception on {candidate_name}: {type(e).__name__}: {e}")
            continue

    return {
        "available": False,
        "error": "Gemini vision analysis is temporarily unavailable.",
        "source": "Google Gemini Vision",
    }

