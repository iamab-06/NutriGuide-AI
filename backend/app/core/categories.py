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
}

NUM_CLASSES = len(SUPPORTED_CATEGORIES)
