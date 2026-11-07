"""
NutriGuide AI - Supported Food Categories
These are the Food-101 categories the classifier is trained to recognize.
"""

SUPPORTED_CATEGORIES = [
    "apple_pie",
    "caesar_salad",
    "chicken_curry",
    "chocolate_cake",
    "donuts",
    "french_fries",
    "fried_rice",
    "hamburger",
    "hot_dog",
    "ice_cream",
    "omelette",
    "pancakes",
    "pizza",
    "ramen",
    "samosa",
    "spaghetti_bolognese",
    "spring_rolls",
    "steak",
    "sushi",
    "waffles",
]

# Human-readable display names
CATEGORY_DISPLAY_NAMES = {
    "apple_pie": "Apple Pie",
    "caesar_salad": "Caesar Salad",
    "chicken_curry": "Chicken Curry",
    "chocolate_cake": "Chocolate Cake",
    "donuts": "Donuts",
    "french_fries": "French Fries",
    "fried_rice": "Fried Rice",
    "hamburger": "Hamburger",
    "hot_dog": "Hot Dog",
    "ice_cream": "Ice Cream",
    "omelette": "Omelette",
    "pancakes": "Pancakes",
    "pizza": "Pizza",
    "ramen": "Ramen",
    "samosa": "Samosa",
    "spaghetti_bolognese": "Spaghetti Bolognese",
    "spring_rolls": "Spring Rolls",
    "steak": "Steak",
    "sushi": "Sushi",
    "waffles": "Waffles",
}

# USDA search queries for each category (normalized food name for API lookup)
USDA_SEARCH_QUERIES = {
    "apple_pie": "apple pie",
    "caesar_salad": "caesar salad",
    "chicken_curry": "chicken curry",
    "chocolate_cake": "chocolate cake",
    "donuts": "glazed donut",
    "french_fries": "french fries",
    "fried_rice": "fried rice",
    "hamburger": "hamburger",
    "hot_dog": "hot dog",
    "ice_cream": "vanilla ice cream",
    "omelette": "egg omelette",
    "pancakes": "pancakes plain",
    "pizza": "cheese pizza",
    "ramen": "ramen noodles",
    "samosa": "samosa",
    "spaghetti_bolognese": "spaghetti bolognese",
    "spring_rolls": "spring rolls",
    "steak": "beef steak",
    "sushi": "sushi rolls",
    "waffles": "waffles plain",
    "tiramisu": "tiramisu",
}

NUM_CLASSES = len(SUPPORTED_CATEGORIES)

# Verified USDA FoodData Central Reference Data (per 100g)
# Serves as fallback if USDA API hits HTTP 429 (rate limits on DEMO_KEY) or is offline
USDA_REFERENCE_DATA = {
    "apple_pie": {"food_name": "Apple pie", "calories": 237.0, "protein": 1.9, "carbohydrates": 34.0, "fat": 11.0, "sugar": 16.0, "fiber": 1.6, "sodium": 217.0, "cholesterol": 0.0, "saturated_fat": 2.8, "fdcId": 171688},
    "caesar_salad": {"food_name": "Caesar salad with dressing", "calories": 189.0, "protein": 5.3, "carbohydrates": 8.0, "fat": 16.0, "sugar": 1.8, "fiber": 1.5, "sodium": 480.0, "cholesterol": 18.0, "saturated_fat": 3.2, "fdcId": 1100388},
    "chicken_curry": {"food_name": "Chicken curry", "calories": 165.0, "protein": 14.5, "carbohydrates": 6.2, "fat": 9.2, "sugar": 2.1, "fiber": 1.2, "sodium": 450.0, "cholesterol": 52.0, "saturated_fat": 2.4, "fdcId": 172847},
    "chocolate_cake": {"food_name": "Chocolate cake with frosting", "calories": 371.0, "protein": 4.9, "carbohydrates": 52.0, "fat": 17.0, "sugar": 38.0, "fiber": 2.8, "sodium": 300.0, "cholesterol": 30.0, "saturated_fat": 5.5, "fdcId": 171698},
    "donuts": {"food_name": "Glazed yeast donut", "calories": 452.0, "protein": 4.9, "carbohydrates": 51.0, "fat": 25.0, "sugar": 27.0, "fiber": 1.5, "sodium": 326.0, "cholesterol": 21.0, "saturated_fat": 6.8, "fdcId": 171708},
    "french_fries": {"food_name": "French fries, restaurant style", "calories": 312.0, "protein": 3.4, "carbohydrates": 41.0, "fat": 15.0, "sugar": 0.3, "fiber": 3.8, "sodium": 210.0, "cholesterol": 0.0, "saturated_fat": 2.3, "fdcId": 170708},
    "fried_rice": {"food_name": "Fried rice with vegetables and egg", "calories": 163.0, "protein": 5.2, "carbohydrates": 28.0, "fat": 3.5, "sugar": 0.8, "fiber": 1.2, "sodium": 390.0, "cholesterol": 35.0, "saturated_fat": 0.8, "fdcId": 1101582},
    "hamburger": {"food_name": "Hamburger, single patty with condiments", "calories": 295.0, "protein": 17.0, "carbohydrates": 24.0, "fat": 14.0, "sugar": 4.2, "fiber": 1.5, "sodium": 480.0, "cholesterol": 42.0, "saturated_fat": 5.2, "fdcId": 173322},
    "hot_dog": {"food_name": "Frankfurter (hot dog) in bun", "calories": 290.0, "protein": 10.0, "carbohydrates": 24.0, "fat": 17.0, "sugar": 4.0, "fiber": 1.0, "sodium": 560.0, "cholesterol": 33.0, "saturated_fat": 6.0, "fdcId": 173335},
    "ice_cream": {"food_name": "Vanilla ice cream", "calories": 207.0, "protein": 3.5, "carbohydrates": 24.0, "fat": 11.0, "sugar": 21.0, "fiber": 0.7, "sodium": 80.0, "cholesterol": 44.0, "saturated_fat": 6.8, "fdcId": 171887},
    "omelette": {"food_name": "Egg omelette, plain", "calories": 154.0, "protein": 11.0, "carbohydrates": 0.6, "fat": 12.0, "sugar": 0.4, "fiber": 0.0, "sodium": 142.0, "cholesterol": 372.0, "saturated_fat": 3.3, "fdcId": 172183},
    "pancakes": {"food_name": "Pancakes, plain", "calories": 227.0, "protein": 6.4, "carbohydrates": 28.0, "fat": 10.0, "sugar": 4.3, "fiber": 1.4, "sodium": 439.0, "cholesterol": 59.0, "saturated_fat": 2.1, "fdcId": 172782},
    "pizza": {"food_name": "Cheese pizza, regular crust", "calories": 266.0, "protein": 10.5, "carbohydrates": 33.0, "fat": 10.0, "sugar": 3.6, "fiber": 2.3, "sodium": 598.0, "cholesterol": 17.0, "saturated_fat": 4.5, "fdcId": 173292},
    "ramen": {"food_name": "Ramen noodle soup with broth", "calories": 436.0, "protein": 10.0, "carbohydrates": 65.0, "fat": 16.0, "sugar": 2.0, "fiber": 3.0, "sodium": 1820.0, "cholesterol": 0.0, "saturated_fat": 7.5, "fdcId": 173482},
    "samosa": {"food_name": "Samosa, vegetable filled", "calories": 262.0, "protein": 4.0, "carbohydrates": 32.0, "fat": 13.0, "sugar": 1.5, "fiber": 2.5, "sodium": 420.0, "cholesterol": 5.0, "saturated_fat": 3.5, "fdcId": 1101890},
    "spaghetti_bolognese": {"food_name": "Spaghetti bolognese with meat sauce", "calories": 132.0, "protein": 7.2, "carbohydrates": 15.0, "fat": 4.8, "sugar": 2.4, "fiber": 1.6, "sodium": 340.0, "cholesterol": 18.0, "saturated_fat": 1.6, "fdcId": 1101901},
    "spring_rolls": {"food_name": "Vegetable spring rolls", "calories": 153.0, "protein": 3.5, "carbohydrates": 18.0, "fat": 7.5, "sugar": 1.8, "fiber": 1.8, "sodium": 380.0, "cholesterol": 0.0, "saturated_fat": 1.2, "fdcId": 1101920},
    "steak": {"food_name": "Beef steak, tenderloin, cooked", "calories": 271.0, "protein": 25.0, "carbohydrates": 0.0, "fat": 19.0, "sugar": 0.0, "fiber": 0.0, "sodium": 65.0, "cholesterol": 85.0, "saturated_fat": 7.8, "fdcId": 170208},
    "sushi": {"food_name": "Sushi, mixed rolls with fish and vegetables", "calories": 142.0, "protein": 5.8, "carbohydrates": 25.0, "fat": 2.1, "sugar": 4.5, "fiber": 1.5, "sodium": 480.0, "cholesterol": 12.0, "saturated_fat": 0.4, "fdcId": 1101935},
    "waffles": {"food_name": "Waffles, plain", "calories": 291.0, "protein": 7.9, "carbohydrates": 33.0, "fat": 14.0, "sugar": 2.0, "fiber": 1.8, "sodium": 511.0, "cholesterol": 69.0, "saturated_fat": 2.4, "fdcId": 172788},
    "tiramisu": {"food_name": "Tiramisu", "calories": 353.0, "protein": 5.65, "carbohydrates": 29.4, "fat": 23.9, "sugar": 18.7, "fiber": 0.6, "sodium": 173.0, "cholesterol": 121.0, "saturated_fat": 13.3, "fdcId": 2705702},
    # Common staple nutritional reference foods
    "chicken_breast": {"food_name": "Chicken breast, cooked, skinless", "calories": 165.0, "protein": 31.0, "carbohydrates": 0.0, "fat": 3.6, "sugar": 0.0, "fiber": 0.0, "sodium": 74.0, "cholesterol": 85.0, "saturated_fat": 1.0, "fdcId": 171077},
    "egg": {"food_name": "Whole egg, large (approx 50g each, 6.3g protein/egg)", "calories": 143.0, "protein": 12.6, "carbohydrates": 0.7, "fat": 9.5, "sugar": 0.4, "fiber": 0.0, "sodium": 142.0, "cholesterol": 372.0, "saturated_fat": 3.1, "fdcId": 171287},
    "salmon": {"food_name": "Atlantic salmon, cooked", "calories": 208.0, "protein": 22.0, "carbohydrates": 0.0, "fat": 13.0, "sugar": 0.0, "fiber": 0.0, "sodium": 61.0, "cholesterol": 63.0, "saturated_fat": 3.1, "fdcId": 173686},
    "tofu": {"food_name": "Tofu, firm", "calories": 83.0, "protein": 10.0, "carbohydrates": 2.3, "fat": 5.3, "sugar": 0.5, "fiber": 1.0, "sodium": 7.0, "cholesterol": 0.0, "saturated_fat": 0.8, "fdcId": 172448},
    "banana": {"food_name": "Banana, fresh", "calories": 89.0, "protein": 1.1, "carbohydrates": 22.8, "fat": 0.3, "sugar": 12.2, "fiber": 2.6, "sodium": 1.0, "cholesterol": 0.0, "saturated_fat": 0.1, "fdcId": 173944},
    "oats": {"food_name": "Rolled oats, whole grain", "calories": 389.0, "protein": 16.9, "carbohydrates": 66.3, "fat": 6.9, "sugar": 0.0, "fiber": 10.6, "sodium": 2.0, "cholesterol": 0.0, "saturated_fat": 1.2, "fdcId": 173904},
    "greek_yogurt": {"food_name": "Greek yogurt, plain", "calories": 73.0, "protein": 10.0, "carbohydrates": 3.9, "fat": 2.0, "sugar": 3.6, "fiber": 0.0, "sodium": 46.0, "cholesterol": 6.0, "saturated_fat": 1.2, "fdcId": 173432},
}

# ---------------------------------------------------------------------------
# Full Food-101 (101 categories) Reference Catalog
# ---------------------------------------------------------------------------
import os
import json

_f101_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "food101_names.json")
ALL_FOOD101_CATEGORIES = []
FOOD101_DISPLAY_NAMES = {}

if os.path.exists(_f101_path):
    try:
        with open(_f101_path, "r", encoding="utf-8") as f:
            raw_map = json.load(f)
            # Keys are indices "0"..."100", values are category keys
            sorted_indices = sorted([int(k) for k in raw_map.keys()])
            ALL_FOOD101_CATEGORIES = [raw_map[str(idx)] for idx in sorted_indices]
            FOOD101_DISPLAY_NAMES = {
                cat: cat.replace("_", " ").title() for cat in ALL_FOOD101_CATEGORIES
            }
    except Exception:
        pass

if not ALL_FOOD101_CATEGORIES:
    ALL_FOOD101_CATEGORIES = list(SUPPORTED_CATEGORIES)
    FOOD101_DISPLAY_NAMES = dict(CATEGORY_DISPLAY_NAMES)

