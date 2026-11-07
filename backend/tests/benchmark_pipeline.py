"""
NutriGuide AI - Comprehensive Performance & Accuracy Benchmark Suite
Measures actual latency, TTFT, cache hit rates, database lookups, and validation checks.
All measurements are empirically tested and recorded.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import time
import asyncio
import io
from PIL import Image

async def run_all_benchmarks():
    print("=" * 60)
    print("NUTRIGUIDE AI — SYSTEM PERFORMANCE & ACCURACY BENCHMARK")
    print("=" * 60)

    # 1. Computer Vision Classifier Latency
    print("\n[1] Computer Vision (MobileNetV3):")
    from app.services.classifier import FoodClassifier
    clf = FoodClassifier()
    img = Image.new("RGB", (224, 224), color=(128, 128, 128))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    img_bytes = buf.getvalue()

    # Warmup
    _ = clf.predict(img_bytes)
    times = []
    for _ in range(10):
        t0 = time.perf_counter()
        _ = clf.predict(img_bytes)
        times.append((time.perf_counter() - t0) * 1000)
    avg_clf = sum(times) / len(times)
    min_clf = min(times)
    max_clf = max(times)
    p95_clf = sorted(times)[int(len(times) * 0.95)]
    print(f"  MobileNetV3 Average: {avg_clf:.2f}ms")
    print(f"  MobileNetV3 Min:     {min_clf:.2f}ms")
    print(f"  MobileNetV3 Max:     {max_clf:.2f}ms")
    print(f"  MobileNetV3 p95:     {p95_clf:.2f}ms")

    # 2. Local Curated Food Database (SQLite)
    print("\n[2] Curated Food Database (SQLite - Indian & Global Staples):")
    from app.data.food_database import get_local_food_db
    db = get_local_food_db()
    test_queries = ["roti", "idli", "paneer", "dal tadka", "chicken breast", "banana", "salmon"]
    db_times = []
    for q in test_queries:
        t0 = time.perf_counter()
        res = db.search_by_term(q)
        dt = (time.perf_counter() - t0) * 1000
        db_times.append(dt)
        first_item = res["canonical_name"] if res else "None"
        print(f"  Lookup '{q}': {dt:.3f}ms -> Matched: {first_item}")
    avg_db = sum(db_times) / len(db_times)
    print(f"  Average SQLite Lookup Latency: {avg_db:.3f}ms across {len(test_queries)} queries")

    # 3. RAG Knowledge Base Retrieval
    print("\n[3] RAG Semantic Knowledge Base Retrieval:")
    from app.rag.rag_service import get_rag_service
    t0 = time.perf_counter()
    rag = get_rag_service()
    init_ms = (time.perf_counter() - t0) * 1000
    print(f"  RAG Service Init / Access: {init_ms:.2f}ms")

    rag_queries = ["protein in dal", "keto diet guidelines", "glycemic index of rice", "calcium in paneer"]
    rag_times = []
    for rq in rag_queries:
        t0 = time.perf_counter()
        ctx = rag.get_context_string(rq, k=3)
        dt = (time.perf_counter() - t0) * 1000
        rag_times.append(dt)
        print(f"  RAG Query '{rq}': {dt:.2f}ms ({len(ctx)} chars retrieved)")
    avg_rag = sum(rag_times) / len(rag_times)
    print(f"  Average Warm RAG Retrieval: {avg_rag:.2f}ms")

    # 4. Cache Performance & Single-Flight Coalescing
    print("\n[4] Asynchronous TTL LRU Cache Performance:")
    from app.services.cache import nutrition_cache, search_cache
    from app.services.nutrition import get_nutrition_for_food

    # Measure un-cached vs cached for several items
    test_foods = ["apple", "spinach", "egg", "oats"]
    uncached_times = []
    for f in test_foods:
        # Clear cache for this key to measure fresh lookup
        nutrition_cache.invalidate(f)
        t0 = time.perf_counter()
        res = await get_nutrition_for_food(f)
        uncached_times.append((time.perf_counter() - t0) * 1000)

    cached_times = []
    for f in test_foods:
        t0 = time.perf_counter()
        res = await get_nutrition_for_food(f)
        cached_times.append((time.perf_counter() - t0) * 1000)

    avg_uncached = sum(uncached_times) / len(uncached_times)
    avg_cached = sum(cached_times) / len(cached_times)
    speedup = avg_uncached / avg_cached if avg_cached > 0 else 1.0

    print(f"  Average Fresh Nutrition Lookup:  {avg_uncached:.2f}ms")
    print(f"  Average Cached Nutrition Lookup: {avg_cached:.2f}ms")
    print(f"  Cache Acceleration Factor:       {speedup:.1f}x faster")
    stats = nutrition_cache.get_stats()
    print(f"  Cache Stats: Hits={stats['hits']}, Misses={stats['misses']}, Hit Rate={stats['hit_rate_pct']}%")

    # 5. Numerical Validation & Sanity Verification
    print("\n[5] Numerical Validation Layer (Atwater & Macro Balance):")
    from app.services.validator import validate_and_sanitize_nutrition, ValidationResult
    t0 = time.perf_counter()
    # Test valid item
    valid_data = {
        "calories": 200.0,
        "protein": 10.0,
        "carbohydrates": 25.0,
        "fat": 7.0,
        "sugar": 5.0,
        "fiber": 3.0,
    }
    san_v, res_v = validate_and_sanitize_nutrition(valid_data, basis="per 100g", source="Test Standard")

    # Test invalid item (impossible energy balance / negative macro)
    invalid_data = {
        "calories": 900.0,
        "protein": 5.0,
        "carbohydrates": 5.0,
        "fat": 5.0,
    }
    san_inv, res_inv = validate_and_sanitize_nutrition(invalid_data, basis="per 100g", source="Test Suspicious")
    val_dt = (time.perf_counter() - t0) * 1000

    print(f"  Validation execution time: {val_dt:.3f}ms")
    print(f"  Valid food Atwater balance:   Status={res_v.verification_status}, Valid={res_v.is_valid}, Discrepancy={res_v.atwater_discrepancy_pct}%")
    print(f"  Invalid food caught:          Status={res_inv.verification_status}, Valid={res_inv.is_valid}, Discrepancy={res_inv.atwater_discrepancy_pct}%, Warnings={res_inv.warnings}")

    # 6. LLM Token Streaming & Latency (if Ollama reachable)
    print("\n[6] Generative AI Streaming & TTFT (Ollama / Gemma 3):")
    from app.services.ollama_service import stream_chat_with_context, is_ollama_configured
    if is_ollama_configured():
        t0 = time.perf_counter()
        ttft = None
        token_count = 0
        try:
            async for event in stream_chat_with_context(
                user_message="What is the protein content of chicken breast per 100g?",
                food_context={"food_name": "Chicken Breast", "nutrition": {"calories": 165, "protein": 31, "carbohydrates": 0, "fat": 3.6}},
                history=[]
            ):
                if event.get("event") == "token":
                    if ttft is None:
                        ttft = (time.perf_counter() - t0) * 1000
                    token_count += 1
            total_gen_ms = (time.perf_counter() - t0) * 1000
            print(f"  Time To First Token (TTFT): {ttft:.2f}ms" if ttft else "  TTFT: N/A")
            print(f"  Total Generation Time:       {total_gen_ms:.2f}ms")
            print(f"  Tokens Generated:            {token_count} tokens")
            if total_gen_ms > 0 and token_count > 0:
                print(f"  Generation Throughput:       {token_count / (total_gen_ms / 1000):.2f} tokens/sec")
        except Exception as e:
            print(f"  Ollama test skipped or failed: {e}")
    else:
        print("  Ollama offline, streaming test skipped.")

    print("\n" + "=" * 60)
    print("ALL EMPIRICAL MEASUREMENTS COMPLETED.")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_all_benchmarks())
