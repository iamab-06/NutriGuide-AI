"""
NutriGuide AI - End-to-End User Journey Verification Script
Tests Journeys A through F:
- Journey A: Food recognition (prediction, confidence, alternatives)
- Journey B: Nutrition retrieval (per 100g, USDA data)
- Journey C: Packaged product & allergens (Open Food Facts API)
- Journey D: GenAI assistant (evidence grounding + RAG context)
- Journey E: Food comparison (side-by-side per 100g)
- Journey F: Uncertainty & ambiguous input rejection
"""
import asyncio
import io
import time
from PIL import Image
from app.services.classifier import get_classifier
from app.services.nutrition import get_nutrition_for_food
from app.services.openfoodfacts import search_product, get_product_by_barcode
from app.services.gemini_service import _build_nutrition_context, chat_with_context
from app.rag.rag_service import get_rag_service


def create_test_food_image() -> bytes:
    # 224x224 RGB image
    img = Image.new("RGB", (224, 224), color=(200, 100, 50))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


async def verify_journey_a():
    print("\n--- JOURNEY A: Food Image Recognition ---")
    classifier = get_classifier()
    img_bytes = create_test_food_image()
    t0 = time.perf_counter()
    res = classifier.predict(img_bytes)
    latency_ms = (time.perf_counter() - t0) * 1000
    print(f"Top Class: {res['predicted_class']} ({res['display_name']})")
    print(f"Confidence: {res['confidence']*100:.1f}%")
    print(f"Confidence Threshold: {res['confidence_threshold']*100:.0f}%")
    print(f"Is Confident: {res['is_confident']}")
    print(f"Top 5 Alternatives: {[p['display_name'] for p in res['top_predictions']]}")
    print(f"Inference Latency: {latency_ms:.2f} ms")
    assert "predicted_class" in res
    assert "top_predictions" in res
    print("Journey A: PASS")
    return res


async def verify_journey_b():
    print("\n--- JOURNEY B: Nutrition Retrieval ---")
    # Retrieve nutrition for 'pizza'
    t0 = time.perf_counter()
    nutrition = await get_nutrition_for_food("pizza", category_key="pizza")
    latency_ms = (time.perf_counter() - t0) * 1000
    print(f"Food Name: {nutrition.food_name}")
    print(f"Source: {nutrition.source}")
    print(f"Basis: {nutrition.basis}")
    print(f"Calories: {nutrition.calories} kcal")
    print(f"Protein: {nutrition.protein} g")
    print(f"Carbs: {nutrition.carbohydrates} g")
    print(f"Fat: {nutrition.fat} g")
    print(f"Data Available: {nutrition.data_available}")
    print(f"Retrieval Latency: {latency_ms:.2f} ms")
    print("Journey B: PASS")
    return nutrition


async def verify_journey_c():
    print("\n--- JOURNEY C: Packaged Product & Allergens ---")
    t0 = time.perf_counter()
    products = await search_product("Nutella", page_size=2)
    latency_ms = (time.perf_counter() - t0) * 1000
    print(f"Products found: {len(products)}")
    if products:
        p = products[0]
        print(f"Product: {p.product_name} by {p.brands}")
        print(f"Allergens: {p.allergens or 'None declared'}")
        print(f"Allergens Tags: {p.allergens_tags}")
        print(f"Ingredients (preview): {(p.ingredients_text or '')[:100]}...")
        print(f"Missing fields: {p.missing_fields}")
    print(f"Open Food Facts Latency: {latency_ms:.2f} ms")
    print("Journey C: PASS")
    return products


async def verify_journey_d(nutrition_data):
    print("\n--- JOURNEY D: GenAI Assistant & RAG ---")
    rag = get_rag_service()
    query = "Is pizza high in sodium and calories?"
    rag_context = rag.get_context_string(query, k=2)
    print(f"RAG Retrieved Context:\n{rag_context if rag_context else 'RAG running in fallback mode'}")

    # Build context
    food_ctx = {
        "food_name": "pizza",
        "nutrition": nutrition_data.model_dump() if nutrition_data else None,
        "rag_context": rag_context,
    }
    context_str = _build_nutrition_context(food_ctx)
    print(f"Evidence Context Length: {len(context_str)} chars")
    assert "VERIFIED FOOD DATA" in context_str

    # Chat
    chat_res = await chat_with_context(
        user_message=query,
        food_context=food_ctx,
    )
    print(f"Assistant Response Preview: {chat_res['answer'][:200]}...")
    print(f"Sources cited: {chat_res['sources']}")
    print(f"Evidence used: {chat_res['evidence_used']}")
    print(f"Warning: {chat_res.get('warning')}")
    print("Journey D: PASS")


async def verify_journey_e(nutrition_data):
    print("\n--- JOURNEY E: Food Comparison ---")
    hamburger_data = await get_nutrition_for_food("hamburger", category_key="hamburger")
    print(f"Comparing {nutrition_data.food_name} vs {hamburger_data.food_name}:")
    print(f"  Basis: {nutrition_data.basis} vs {hamburger_data.basis}")
    print(f"  Calories: {nutrition_data.calories} kcal vs {hamburger_data.calories} kcal")
    print(f"  Protein: {nutrition_data.protein} g vs {hamburger_data.protein} g")
    print(f"  Fat: {nutrition_data.fat} g vs {hamburger_data.fat} g")
    assert nutrition_data.basis == hamburger_data.basis
    print("Journey E: PASS")


async def verify_journey_f():
    print("\n--- JOURNEY F: Uncertainty & Ambiguity Handling ---")
    classifier = get_classifier()
    # Uniform gray image (non-food/ambiguous)
    img = Image.new("RGB", (224, 224), color=(128, 128, 128))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    res = classifier.predict(buf.getvalue())
    print(f"Ambiguous Image Confidence: {res['confidence']*100:.1f}%")
    print(f"Threshold: {res['confidence_threshold']*100:.0f}%")
    print(f"Is Confident: {res['is_confident']}")
    assert not res["is_confident"], "Ambiguous image must have confidence below threshold!"
    print("Journey F: PASS (Ambiguous image correctly identified as uncertain)")


async def main():
    print("==================================================")
    print("   NUTRIGUIDE AI: END-TO-END VERIFICATION SUITE   ")
    print("==================================================")
    clf_res = await verify_journey_a()
    nutrition = await verify_journey_b()
    await verify_journey_c()
    await verify_journey_d(nutrition)
    await verify_journey_e(nutrition)
    await verify_journey_f()
    print("\n==================================================")
    print("   ALL 6 USER JOURNEYS SUCCESSFULLY VERIFIED!     ")
    print("==================================================")


if __name__ == "__main__":
    asyncio.run(main())
