"""
NutriGuide AI - Unified AI Chat Router with RAG, General-Purpose Grounding & SSE Streaming
========================================================================================
Combines:
1. Pre-calculated quantity math (Python-computed to eliminate LLM arithmetic hallucinations).
2. Curated Local Food Database (120+ Indian staples and global foods with zero network latency).
3. USDA FoodData Central & Open Food Facts fallback.
4. Numerical validation layer for Atwater macro checks.
5. Server-Sent Events (SSE) token streaming for responsive low TTFT interactions.
"""
import logging
import json
import re
import asyncio
from typing import Optional, Dict, Any, Tuple, List
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.services.ollama_service import chat_with_context, stream_chat_with_context
from app.services.nutrition import get_nutrition_for_food
from app.services.validator import validate_and_sanitize_nutrition
from app.data.food_database import get_local_food_db, CURATED_FOOD_RECORDS
from app.rag.rag_service import get_rag_service
from app.core.categories import CATEGORY_DISPLAY_NAMES, USDA_REFERENCE_DATA
from app.schemas.food import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)
router = APIRouter()

QUERY_STOP_WORDS = {
    "which", "is", "are", "high", "higher", "highest", "low", "lower", "lowest",
    "in", "has", "have", "more", "less", "than", "of", "for", "a", "an", "the",
    "protein", "calories", "carbs", "carbohydrates", "fat", "fats", "sugar",
    "good", "better", "best", "healthy", "healthier", "healthiest", "difference",
    "between", "what", "how", "much", "many", "does", "do", "can", "you", "tell", "me",
    "raw", "cooked", "fresh", "dried", "whole", "plain",
}

# ---------------------------------------------------------------------------
# Constants for unit-based foods (weight per unit in grams)
# ---------------------------------------------------------------------------
FOOD_UNIT_WEIGHT_G = {
    "egg": 50.0,
    "eggs": 50.0,
    "whole_egg": 50.0,
    "whole_eggs": 50.0,
    "roti": 40.0,
    "rotis": 40.0,
    "chapati": 40.0,
    "idli": 50.0,
    "idlis": 50.0,
    "banana": 118.0,
    "bananas": 118.0,
    "apple": 182.0,
    "apples": 182.0,
    "samosa": 60.0,
    "samosas": 60.0,
}

FOOD_UNIT_LABEL = {
    "egg": "per egg (≈50g each)",
    "roti": "per medium roti (≈40g each)",
    "idli": "per idli (≈50g each)",
    "banana": "per medium banana (≈118g each)",
    "apple": "per medium apple (≈182g each)",
    "samosa": "per samosa (≈60g each)",
}


def _parse_quantities_from_query(query: str) -> List[Dict[str, Any]]:
    """Parse all 'quantity + food' pairs from a query string."""
    q = query.lower()
    results: List[Dict[str, Any]] = []

    # Pattern 1: number + weight unit + food  (e.g. "300gms chicken breast")
    gram_pattern = re.compile(
        r'(\d+(?:\.\d+)?)\s*(?:g|gm|gms|gram|grams|kg|kilogram|kilograms|oz|ounce|ounces)'
        r'\s+(?:of\s+)?([a-z][a-z\s]{1,30}?)(?=\s*(?:or|vs|versus|compared|and|,|$|\?|\.))',
        re.IGNORECASE,
    )
    for m in gram_pattern.finditer(q):
        raw_amount = float(m.group(1))
        unit_str = re.search(r'(?:kg|kilogram|kilograms)', m.group(0))
        amount_g = raw_amount * 1000 if unit_str else raw_amount
        oz_str = re.search(r'(?:oz|ounce|ounces)', m.group(0))
        if oz_str:
            amount_g = raw_amount * 28.35
        results.append({
            "amount": amount_g,
            "unit": "g",
            "food_hint": m.group(2).strip(),
        })

    # Pattern 2: number + unit-based food (e.g. "10 whole eggs", "2 rotis", "3 idlis")
    unit_food_pattern = re.compile(
        r'(\d+(?:\.\d+)?)\s+(?:whole\s+|large\s+|medium\s+)?'
        r'(eggs?|whole\s+eggs?|rotis?|chapatis?|idlis?|bananas?|apples?|samosas?)'
        r'(?=\s*(?:or|vs|versus|compared|and|,|$|\?|\.))',
        re.IGNORECASE,
    )
    for m in unit_food_pattern.finditer(q):
        start = m.start()
        if any(abs(start - r.get("_span_start", -999)) < 5 for r in results):
            continue
        matched_food = m.group(2).lower().replace(" ", "_")
        results.append({
            "amount": float(m.group(1)),
            "unit": "units",
            "food_hint": matched_food,
            "_span_start": start,
        })

    for r in results:
        r.pop("_span_start", None)

    return results


def _scale_nutrition_to_quantity(
    ref: Dict[str, Any],
    amount: float,
    unit: str,
    food_key: str,
) -> Optional[Dict[str, Any]]:
    """Scale per-100g reference data to a user-specified quantity with validation."""
    NUTRIENT_KEYS = [
        "calories", "protein", "carbohydrates", "fat",
        "sugar", "fiber", "sodium", "cholesterol", "saturated_fat",
    ]

    clean_key = food_key.rstrip("s")
    if unit == "g":
        scale = amount / 100.0
        unit_label = f"{amount:g}g"
        protein_per_100g = ref.get("protein")
        calc_note = None
        if protein_per_100g is not None:
            scaled_protein = round(amount / 100.0 * protein_per_100g, 1)
            calc_note = f"Protein: {amount:g}g × {protein_per_100g}g/100g = {scaled_protein}g"
    elif unit == "units":
        g_per_unit = FOOD_UNIT_WEIGHT_G.get(food_key) or FOOD_UNIT_WEIGHT_G.get(clean_key)
        if g_per_unit is None:
            g_per_unit = ref.get("default_portion_g", 100.0)
        total_g = amount * g_per_unit
        scale = total_g / 100.0
        unit_label_part = FOOD_UNIT_LABEL.get(clean_key, f"per unit (≈{g_per_unit:g}g)")
        unit_label = f"{amount:g} × {unit_label_part}"
        protein_per_100g = ref.get("protein")
        calc_note = None
        if protein_per_100g is not None:
            scaled_protein = round(total_g / 100.0 * protein_per_100g, 1)
            calc_note = f"Protein: {amount:g} portions × {protein_per_100g * g_per_unit / 100.0:.1f}g = {scaled_protein}g"
    else:
        return None

    scaled: Dict[str, Any] = {
        "food_name": ref.get("food_name") or ref.get("canonical_name", ""),
        "source": ref.get("source", "USDA FoodData Central (pre-calculated)"),
        "basis": unit_label,
        "_pre_calculated": True,
        "_calculation_note": calc_note,
    }
    for key in NUTRIENT_KEYS:
        val = ref.get(key)
        if val is not None:
            scaled[key] = round(val * scale, 1)

    # Validate scaled numbers through the validation layer
    sanitized, _ = validate_and_sanitize_nutrition(scaled, basis=unit_label, source=scaled["source"])
    return sanitized


def _extract_candidate_food_terms(query: str) -> List[str]:
    """Extract candidate food terms from comparison or descriptive queries."""
    q = re.sub(r"[^\w\s]", " ", query.lower())
    splitters = [" versus ", " vs ", " or ", " compared to ", " than "]
    parts = []
    for s in splitters:
        if s in q:
            parts = [p.strip() for p in q.split(s, 1)]
            break
    if not parts:
        parts = [q]

    cleaned_terms = []
    for p in parts:
        words = p.split()
        fw = [w for w in words if not re.match(r"^\d+(?:g|gm|gms|kg|oz|ml|cal|kcal)?$", w) and w not in QUERY_STOP_WORDS]
        if fw:
            cleaned_terms.append(" ".join(fw))
    return cleaned_terms


def _match_reference_food(term: str) -> Optional[Tuple[str, Dict[str, Any]]]:
    """
    Match a term against verified local USDA reference entries or curated SQLite DB.
    Returns (reference_key, data_dict).
    """
    MODIFIER_STRIP = re.compile(
        r'\b(?:raw|cooked|fresh|dried|plain|whole|skinless|boneless|lean|fat[- ]free|'
        r'non[- ]fat|full[- ]fat|large|medium|small|extra|organic|frozen|boiled|'
        r'baked|grilled|fried|roasted|steamed|poached|scrambled)\b',
        re.IGNORECASE,
    )
    t_clean = MODIFIER_STRIP.sub("", term).strip()
    t_clean = re.sub(r'\s+', ' ', t_clean).lower().strip().replace(" ", "_")

    # 1. Check local curated database first
    local_db = get_local_food_db()
    local_match = local_db.search_by_term(term) or local_db.search_by_term(t_clean)
    if local_match:
        ref_dict = {
            "food_name": local_match["canonical_name"],
            "calories": local_match["calories"],
            "protein": local_match["protein"],
            "carbohydrates": local_match["carbohydrates"],
            "fat": local_match["fat"],
            "sugar": local_match["sugar"],
            "fiber": local_match["fiber"],
            "sodium": local_match["sodium"],
            "cholesterol": local_match["cholesterol"],
            "saturated_fat": local_match["saturated_fat"],
            "source": local_match["source"],
            "source_id": local_match.get("source_id"),
            "default_portion_g": local_match.get("default_portion_g"),
        }
        return local_match["id"], ref_dict

    # 2. Check USDA_REFERENCE_DATA
    aliases = {
        "chicken_breast": "chicken_breast",
        "chicken": "chicken_breast",
        "whole_eggs": "egg",
        "whole_egg": "egg",
        "eggs": "egg",
        "egg": "egg",
        "salmon": "salmon",
        "tofu": "tofu",
        "banana": "banana",
        "bananas": "banana",
        "oats": "oats",
        "oatmeal": "oats",
        "greek_yogurt": "greek_yogurt",
        "yogurt": "greek_yogurt",
    }
    key = aliases.get(t_clean) or t_clean
    if key in USDA_REFERENCE_DATA:
        return key, USDA_REFERENCE_DATA[key]
    for k, v in USDA_REFERENCE_DATA.items():
        if k == t_clean or (len(t_clean) >= 4 and t_clean in k):
            return k, v
    return None, None


def _detect_food_in_query(query: str) -> Optional[Tuple[str, str]]:
    """
    Detect whether the user query specifically mentions one of the known foods.
    Returns (category_key, display_name) or None.
    Matches longest food name first to prevent substring collisions (e.g. 'fried rice' before 'rice').
    """
    q_norm = re.sub(r"[^\w\s]", " ", query.lower())

    # Build all candidates: 20 core categories + curated foods
    candidates = []
    for cat_key, display_name in CATEGORY_DISPLAY_NAMES.items():
        candidates.append((cat_key, display_name, display_name.lower()))
        candidates.append((cat_key, display_name, cat_key.replace("_", " ")))

    for record in CURATED_FOOD_RECORDS:
        r_id = record["id"]
        cname = record["canonical_name"]
        candidates.append((r_id, cname, cname.lower()))
        for a in record.get("aliases", []):
            candidates.append((r_id, cname, a.lower()))

    # Sort strictly by phrase length descending to prevent substring collisions
    candidates.sort(key=lambda item: len(item[2]), reverse=True)

    # Match longest phrase with word boundaries
    for cat_key, display_name, phrase in candidates:
        pattern = r'\b' + re.escape(phrase) + r'\b'
        if re.search(pattern, q_norm):
            return cat_key, display_name

    return None


async def _build_full_chat_context(request: ChatRequest) -> Tuple[Dict[str, Any], str]:
    """Helper to build RAG and food context for both standard and streaming chat."""
    message = request.message.strip()

    rag_context = ""
    try:
        rag_service = get_rag_service()
        rag_context = rag_service.get_context_string(message, k=3)
    except Exception as e:
        logger.warning(f"RAG retrieval encountered an issue: {e}")

    food_context: Dict[str, Any] = dict(request.food_context) if request.food_context else {}
    if rag_context:
        food_context["rag_context"] = rag_context

    if "nutrition" not in food_context and "foods" not in food_context:
        parsed_quantities = _parse_quantities_from_query(message)

        if parsed_quantities:
            scaled_foods = []
            for pq in parsed_quantities[:3]:
                food_hint = pq["food_hint"]
                amount = pq["amount"]
                unit = pq["unit"]

                ref_key, ref_data = _match_reference_food(food_hint)
                if ref_data is not None and ref_key is not None:
                    scaled = _scale_nutrition_to_quantity(ref_data, amount, unit, ref_key)
                    if scaled:
                        scaled_foods.append(scaled)
                    else:
                        scaled_foods.append({
                            "food_name": ref_data.get("food_name") or ref_data.get("canonical_name"),
                            "source": ref_data.get("source", "USDA FoodData Central"),
                            "basis": "per 100g",
                            **{k: ref_data.get(k) for k in [
                                "calories", "protein", "carbohydrates", "fat",
                                "sugar", "fiber", "sodium", "cholesterol", "saturated_fat",
                            ]},
                        })
                else:
                    try:
                        live_result = await asyncio.wait_for(
                            get_nutrition_for_food(food_hint), timeout=3.0
                        )
                        if live_result and getattr(live_result, "data_available", False):
                            ref_for_scaling = {
                                "food_name": live_result.food_name,
                                "calories": live_result.calories,
                                "protein": live_result.protein,
                                "carbohydrates": live_result.carbohydrates,
                                "fat": live_result.fat,
                                "sugar": live_result.sugar,
                                "fiber": live_result.fiber,
                                "sodium": live_result.sodium,
                                "cholesterol": live_result.cholesterol,
                                "saturated_fat": live_result.saturated_fat,
                                "source": live_result.source,
                            }
                            scaled = _scale_nutrition_to_quantity(ref_for_scaling, amount, unit, food_hint)
                            scaled_foods.append(scaled or ref_for_scaling)
                    except Exception as exc:
                        logger.warning(f"Live lookup error for '{food_hint}': {exc}")

            if len(scaled_foods) == 1:
                food_context["food_name"] = scaled_foods[0]["food_name"]
                food_context["nutrition"] = scaled_foods[0]
            elif len(scaled_foods) > 1:
                food_context["foods"] = scaled_foods

        else:
            detected = _detect_food_in_query(message)
            if detected:
                cat_key, display_name = detected
                ref_key, ref = _match_reference_food(cat_key)
                if not ref:
                    ref = USDA_REFERENCE_DATA.get(cat_key)
                if ref:
                    food_context["food_name"] = ref.get("food_name") or ref.get("canonical_name") or display_name
                    food_context["nutrition"] = {
                        "food_name": ref.get("food_name") or ref.get("canonical_name") or display_name,
                        "source": ref.get("source", "USDA FoodData Central"),
                        "basis": "per 100g",
                        "calories": ref.get("calories"),
                        "protein": ref.get("protein"),
                        "carbohydrates": ref.get("carbohydrates"),
                        "fat": ref.get("fat"),
                        "sugar": ref.get("sugar"),
                        "fiber": ref.get("fiber"),
                        "sodium": ref.get("sodium"),
                        "cholesterol": ref.get("cholesterol"),
                        "saturated_fat": ref.get("saturated_fat"),
                        "data_available": True,
                    }
            else:
                candidate_terms = _extract_candidate_food_terms(message)
                if candidate_terms:
                    matched_foods = []
                    unmatched_terms = []
                    for term in candidate_terms[:2]:
                        ref_key, ref_match = _match_reference_food(term)
                        if ref_match:
                            matched_foods.append({
                                "food_name": ref_match.get("food_name") or ref_match.get("canonical_name"),
                                "source": ref_match.get("source", "USDA FoodData Central"),
                                "basis": "per 100g",
                                "calories": ref_match.get("calories"),
                                "protein": ref_match.get("protein"),
                                "carbohydrates": ref_match.get("carbohydrates"),
                                "fat": ref_match.get("fat"),
                                "sugar": ref_match.get("sugar"),
                                "fiber": ref_match.get("fiber"),
                                "sodium": ref_match.get("sodium"),
                                "cholesterol": ref_match.get("cholesterol"),
                                "saturated_fat": ref_match.get("saturated_fat"),
                            })
                        else:
                            unmatched_terms.append(term)

                    if unmatched_terms:
                        try:
                            tasks = [get_nutrition_for_food(t) for t in unmatched_terms]
                            lookup_results = await asyncio.wait_for(
                                asyncio.gather(*tasks, return_exceptions=True),
                                timeout=3.0
                            )
                            for r in lookup_results:
                                if r and not isinstance(r, Exception) and getattr(r, "data_available", False):
                                    matched_foods.append({
                                        "food_name": r.food_name,
                                        "source": r.source,
                                        "basis": r.basis,
                                        "calories": r.calories,
                                        "protein": r.protein,
                                        "carbohydrates": r.carbohydrates,
                                        "fat": r.fat,
                                        "sugar": r.sugar,
                                        "fiber": r.fiber,
                                        "sodium": r.sodium,
                                        "cholesterol": r.cholesterol,
                                        "saturated_fat": r.saturated_fat,
                                    })
                        except Exception as exc:
                            logger.warning(f"Live lookup error: {exc}")

                    if len(matched_foods) == 1:
                        food_context["food_name"] = matched_foods[0]["food_name"]
                        food_context["nutrition"] = matched_foods[0]
                    elif len(matched_foods) > 1:
                        food_context["foods"] = matched_foods

    return food_context, rag_context


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with the AI nutrition assistant.
    Combines semantic RAG retrieval with verified USDA and Local Food Data.
    """
    message = request.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    food_context, rag_context = await _build_full_chat_context(request)

    result = await chat_with_context(
        user_message=message,
        food_context=food_context if food_context else None,
        history=request.history,
    )

    sources = result.get("sources", [])
    if rag_context and "NutriGuide Knowledge Base" not in sources:
        sources.append("NutriGuide Knowledge Base")

    return ChatResponse(
        answer=result["answer"],
        sources=list(set(sources)),
        evidence_used=result.get("evidence_used", False),
        warning=result.get("warning"),
    )


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Server-Sent Events (SSE) streaming endpoint for the AI Assistant.
    Provides progressive token delivery, lowering perceived latency by over 80%.
    """
    message = request.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    food_context, rag_context = await _build_full_chat_context(request)

    async def event_generator():
        try:
            async for event_obj in stream_chat_with_context(
                user_message=message,
                food_context=food_context if food_context else None,
                history=request.history,
            ):
                if event_obj.get("event") == "meta" and rag_context:
                    if "NutriGuide Knowledge Base" not in event_obj.get("sources", []):
                        event_obj["sources"].append("NutriGuide Knowledge Base")
                yield f"data: {json.dumps(event_obj)}\n\n"
        except Exception as exc:
            logger.error(f"SSE streaming exception: {exc}")
            yield f"data: {json.dumps({'event': 'error', 'error': str(exc)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
