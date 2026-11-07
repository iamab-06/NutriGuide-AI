"""
NutriGuide AI - End-to-End 5 User Journeys Verification Script
Tests all 5 user journeys through the frontend Vite proxy (http://localhost:5173).
"""
import io
import sys
import httpx
from PIL import Image

BASE_URL = "http://localhost:5173"


def test_journey_1():
    print("==================================================")
    print("1. NUTRITION INFORMATION: Search 'pizza'")
    print("==================================================")
    r = httpx.get(f"{BASE_URL}/api/nutrition/search?q=pizza", timeout=15.0)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.json()
    assert "results" in data, "No 'results' key in response"
    assert len(data["results"]) > 0, "Expected at least 1 result"
    first = data["results"][0]
    print(f"PASS: Found {len(data['results'])} food results.")
    print(f"      Top match: {first['description']} (FDC ID: {first['fdcId']})")

    # Fetch details for the first food
    r_detail = httpx.get(f"{BASE_URL}/api/nutrition/{first['description']}", timeout=15.0)
    assert r_detail.status_code == 200
    n = r_detail.json()
    print(f"      Nutrients per 100g: Calories={n.get('calories')} kcal, "
          f"Protein={n.get('protein')}g, Carbs={n.get('carbohydrates')}g, Fat={n.get('fat')}g")


def test_journey_2():
    print("\n==================================================")
    print("2. INGREDIENTS & ALLERGENS: Search 'Nutella'")
    print("==================================================")
    r = httpx.get(f"{BASE_URL}/api/products/search?q=Nutella", timeout=15.0)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.json()
    assert "results" in data, "No 'results' key in response"
    assert len(data["results"]) > 0, "Expected at least 1 product"
    p = data["results"][0]
    print(f"PASS: Found {len(data['results'])} products.")
    print(f"      Product: {p.get('product_name')} | Brand: {p.get('brands')}")
    print(f"      Allergens: {p.get('allergens')}")
    print(f"      Allergen tags: {p.get('allergens_tags')}")
    print(f"      Barcode: {p.get('barcode')}")


def test_journey_3():
    print("\n==================================================")
    print("3. AI NUTRITION ASSISTANT: Chat 'macros of fried rice'")
    print("==================================================")
    payload = {
        "message": "macros of fried rice",
        "history": []
    }
    r = httpx.post(f"{BASE_URL}/api/chat", json=payload, timeout=25.0)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.json()
    assert "answer" in data, "No 'answer' in response"
    print(f"PASS: Chat endpoint responded (HTTP 200).")
    print(f"      Assistant response: {data['answer']}")
    if data.get("warning"):
        print(f"      Warning/Note: {data['warning']}")


def test_journey_4():
    print("\n==================================================")
    print("4. COMPARE FOODS: Compare 'pizza' and 'hamburger'")
    print("==================================================")
    payload = {"food1": "pizza", "food2": "hamburger"}
    r = httpx.post(f"{BASE_URL}/api/compare", json=payload, timeout=25.0)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.json()
    f1 = data.get("food1", {})
    f2 = data.get("food2", {})
    print(f"PASS: Compared 2 foods on basis: '{data.get('basis')}'.")
    print(f"      Food 1: {f1.get('food_name')} => {f1.get('calories')} kcal, "
          f"{f1.get('protein')}g protein, {f1.get('fat')}g fat")
    print(f"      Food 2: {f2.get('food_name')} => {f2.get('calories')} kcal, "
          f"{f2.get('protein')}g protein, {f2.get('fat')}g fat")
    if data.get("comparison_notes"):
        print(f"      Comparison Notes: {data['comparison_notes']}")


def test_journey_5():
    print("\n==================================================")
    print("5. ANALYZE FOOD: Image Upload & Classification")
    print("==================================================")
    buf = io.BytesIO()
    img = Image.new("RGB", (224, 224), color=(220, 120, 60))
    img.save(buf, format="JPEG")
    buf.seek(0)

    files = {"file": ("food.jpg", buf.getvalue(), "image/jpeg")}
    r = httpx.post(f"{BASE_URL}/api/analyze", files=files, timeout=30.0)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.json()
    clf = data.get("classification", {})
    print(f"PASS: Image processed successfully.")
    print(f"      Top Prediction: {clf.get('display_name')} (class: {clf.get('predicted_class')})")
    print(f"      Confidence: {clf.get('confidence', 0)*100:.1f}% | Threshold: {clf.get('confidence_threshold', 0)*100:.0f}%")
    print(f"      Is Confident: {clf.get('is_confident')}")
    print(f"      System message: {data.get('message')}")
    print(f"      Top 3 alternatives:")
    for alt in clf.get("top_predictions", [])[:3]:
        print(f"        - {alt.get('display_name')}: {alt.get('confidence_pct')}")


if __name__ == "__main__":
    print(f"Connecting to Vite dev server at {BASE_URL}...")
    try:
        health = httpx.get(f"{BASE_URL}/api/health", timeout=5.0).json()
        print(f"Backend status through Vite proxy: {health}\n")
    except Exception as err:
        print(f"ERROR: Cannot reach {BASE_URL}/api/health: {err}")
        sys.exit(1)

    all_passed = True
    for test in [test_journey_1, test_journey_2, test_journey_3, test_journey_4, test_journey_5]:
        try:
            test()
        except Exception as e:
            print(f"FAIL: {e}")
            all_passed = False

    print("\n==================================================")
    if all_passed:
        print("ALL FIVE USER JOURNEYS PASSED END-TO-END!")
    else:
        print("SOME JOURNEYS ENCOUNTERED ISSUES.")
    print("==================================================")
