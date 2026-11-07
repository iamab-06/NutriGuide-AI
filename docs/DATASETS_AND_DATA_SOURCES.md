# NutriGuide AI — Datasets & Data Sources Documentation

**Project:** NutriGuide AI  
**Institution:** Department of Computer Science and Engineering, Siddaganga Institute of Technology  
**Academic Year:** 2026  

---

## 1. Overview of Data Assets

NutriGuide AI integrates five foundational data sources spanning computer vision benchmarks, scientific governmental databases, global crowd-sourced consumer registries, and curated clinical literature:

| # | Data Source | Nature | Primary Role | Size / Scope |
|---|---|---|---|---|
| 1 | **Food-101 Benchmark (All 101 & 20 Subset)** | Image Dataset | Training & evaluation of MobileNetV3-Large | 101,000 images (101 classes) |
| 2 | **Curated Food Database (SQLite)** | Embedded Relational DB | Indian staples & global reference nutrition | 120+ verified foods |
| 3 | **ICMR-NIN IFCT 2017** | Scientific Standard | Indian Food Composition Tables | Key Indian staples (Roti, Dal, Paneer, Idli, Dosa) |
| 4 | **USDA FoodData Central** | Authoritative REST API | Verified macro/micronutrient retrieval | Millions of food records |
| 5 | **Open Food Facts** | Global REST API | Packaged food search, barcodes & allergens | 3+ million commercial items |
| 6 | **Curated Nutrition Knowledge Base** | Domain Text Corpus | Contextual grounding for FAISS RAG | 20 curated nutrition documents |

---

## 2. Food-101 Computer Vision Dataset

### 2.1 Background & Source
- **Origin:** ETH Zurich Computer Vision Laboratory (Bossard et al., European Conference on Computer Vision, 2014).
- **Original Dataset:** 101 food classes, 1,000 images per class (750 train, 250 test), totaling 101,000 real-world food photographs.

### 2.2 Selected 20-Class Target Subset
To build an efficient, highly focused food classifier suitable for commodity hardware and everyday meals, NutriGuide AI selected 20 representative, visually diverse food categories:

| Index | Category Key | Human Display Name | Primary Visual Characteristics |
|---|---|---|---|
| 0 | `apple_pie` | Apple Pie | Baked pastry with lattice or crimped crust, apple filling |
| 1 | `caesar_salad` | Caesar Salad | Romaine lettuce, croutons, parmesan shavings, creamy dressing |
| 2 | `chicken_curry` | Chicken Curry | Spiced sauce/gravy with chicken pieces, often with rice |
| 3 | `chocolate_cake` | Chocolate Cake | Layered dark brown sponge cake with chocolate frosting |
| 4 | `donuts` | Donuts | Toroidal fried dough with glaze, frosting, or sprinkles |
| 5 | `french_fries` | French Fries | Golden-brown potato batons, deep-fried |
| 6 | `fried_rice` | Fried Rice | Stir-fried rice grains with vegetables, eggs, and scallions |
| 7 | `hamburger` | Hamburger | Round bun with meat patty, lettuce, tomato, cheese |
| 8 | `hot_dog` | Hot Dog | Elongated bun with grilled or steamed sausage and condiments |
| 9 | `ice_cream` | Ice Cream | Scooped frozen dairy dessert in bowls or cones |
| 10 | `omelette` | Omelette | Folded fried beaten eggs, often with herbs or fillings |
| 11 | `pancakes` | Pancakes | Flat, circular griddled cakes, often stacked with syrup |
| 12 | `pizza` | Pizza | Flat round dough base with tomato sauce, melted cheese, toppings |
| 13 | `ramen` | Ramen | Japanese wheat noodles in savory broth with sliced toppings |
| 14 | `samosa` | Samosa | Triangular fried pastry with spiced potato/pea filling |
| 15 | `spaghetti_bolognese` | Spaghetti Bolognese | Long thin pasta topped with minced meat tomato sauce |
| 16 | `spring_rolls` | Spring Rolls | Cylindrical rolled thin pastry with vegetable filling |
| 17 | `steak` | Steak | Sliced grilled or seared beef steak with crosshatch marks |
| 18 | `sushi` | Sushi | Rolled nori with vinegared rice and fish or nigiri pieces |
| 19 | `waffles` | Waffles | Leavened batter cooked in a gridded patterned iron |

### 2.3 Split Protocol & Leakage Prevention
- **Training Split:** Exactly 750 images per class (15,000 images total) drawn from the official Food-101 training set.
- **Validation/Test Split:** Exactly 250 unseen images per class (5,000 images total) drawn from the official Food-101 test set.
- **Zero Leakage:** The train and test splits are strictly disjoint, ensuring that model accuracy evaluation (90.64% Top-1, 97.82% Top-3) reflects true generalization to unseen photographs.

---

## 3. USDA FoodData Central Integration

### 3.1 Data Architecture & Endpoints
- **Service Endpoint:** `https://api.nal.usda.gov/fdc/v1`
- **Data Types Queried:** Foundation Foods and SR Legacy (Standard Reference).
- **Search Query Mapping:** Specific food terms are mapped to optimal USDA search targets in `app/core/categories.py`:
  - `samosa` $\to$ `"samosa"`
  - `pizza` $\to$ `"cheese pizza, regular crust"`
  - `chicken_curry` $\to$ `"chicken curry"`
  - `caesar_salad` $\to$ `"caesar salad"`
  - `waffles` $\to$ `"plain waffles"`

### 3.2 Nutrient Extraction Hierarchy
Nutrients are extracted deterministically by official USDA Nutrient ID numbers:
```python
NUTRIENT_IDS = {
    "calories": 1008,       # Energy (kcal)
    "protein": 1003,        # Protein (g)
    "carbohydrates": 1005,  # Carbohydrate, by difference (g)
    "fat": 1004,            # Total lipid (fat) (g)
    "sugar": 2000,          # Sugars, total (g)
    "fiber": 1079,          # Fiber, total dietary (g)
    "sodium": 1093,         # Sodium (mg)
    "cholesterol": 1253,    # Cholesterol (mg)
    "saturated_fat": 1258,  # Fatty acids, total saturated (g)
}
```

### 3.3 Offline Standard Reference Dataset
To ensure 100% uptime when external network access is blocked, during API maintenance, or if rate limits are exceeded, NutriGuide AI incorporates a local reference dictionary in `backend/app/core/categories.py` (`USDA_REFERENCE_DATA`). When invoked, the system clearly marks the data source as:
`source: "USDA FoodData Central (Standard Reference)"`

---

## 4. Open Food Facts Global Database

### 4.1 Search & Barcode Protocol
- **Search API:** `https://world.openfoodfacts.org/cgi/search.pl`
- **Barcode Lookup:** `https://world.openfoodfacts.org/api/v2/product/{barcode}.json`
- **Fields Retrieved:** `product_name`, `brands`, `ingredients_text`, `allergens`, `allergens_tags`, `nutriments`, `image_url`, `code`.

### 4.2 Allergen Safety Handling
Declared allergen tags follow the prefix format `en:milk`, `en:peanuts`, `en:gluten`, etc. The system sanitizes these into user-friendly badges. Crucially, when no allergens are returned, the application displays a cautionary notice:
> **Notice:** No allergens declared in database. This does NOT confirm the product is allergen-free. Always check physical packaging.

---

## 5. Curated Nutrition Knowledge Base (RAG)

The knowledge base in `backend/app/rag/rag_service.py` consists of 20 domain documents structured into title, category, and text:
1. **Macronutrient Balance:** Dietary energy distribution across carbs, proteins, and fats.
2. **Protein Quality & Requirements:** Essential amino acids, complete vs. incomplete proteins.
3. **Dietary Fiber & Digestive Health:** Soluble vs. insoluble fiber, satiety, and gut microbiome.
4. **Carbohydrate Quality & Glycemic Index:** Simple vs. complex carbs, blood glucose spikes.
5. **Dietary Fats:** Saturated, monounsaturated, polyunsaturated, and trans fats.
6. **Sodium & Blood Pressure:** Daily recommended sodium limits (<2,300 mg/day).
7. **Major Food Allergens:** Big-8 allergen profiles (milk, eggs, fish, shellfish, nuts, wheat, soy).
8. **Hydration & Metabolic Function:** Fluid balance and non-caloric beverage choices.
9. **Micronutrient Density:** Vitamins and minerals relative to caloric load.
10. **Nutritional Profile: Pizza:** Cheese and crust macronutrients per 100g.
11. **Nutritional Profile: Samosa:** Pastry carbohydrate and lipid density.
12. **Nutritional Profile: Chicken Curry:** Lean protein and sauce caloric balance.
13. **Nutritional Profile: Sushi:** Fish omega-3 fatty acids and rice carbs.
14. **Nutritional Profile: Caesar Salad:** Leafy greens and dressing calorie variance.
15. **Nutritional Profile: French Fries:** Starch frying lipid absorption.
16. **Nutritional Profile: Hamburger:** Beef protein and bun carbohydrate profile.
17. **Nutritional Profile: Ramen:** Broth sodium concentration.
18. **Nutritional Profile: Pancakes & Waffles:** Syrup sugar spikes.
19. **Nutritional Profile: Chocolate Cake & Donuts:** Dessert sugar and fat moderation.
20. **Nutritional Profile: Steak:** Heme iron, zinc, and high-quality protein.

---

## 6. Curated Food Database (SQLite) & ICMR-NIN IFCT 2017 Dataset

To achieve general-purpose nutrition retrieval without hallucination, NutriGuide AI embeds a high-performance local SQLite database (`backend/app/data/food_database.py`) containing 120+ lab-verified and standardized records.

### 6.1 Data Provenance & Authorities
1. **ICMR - National Institute of Nutrition (NIN) - Indian Food Composition Tables (IFCT 2017):**
   - Authoritative source for regional Indian staples: Roti (Whole Wheat Chapati), Dal Tadka, Dal Makhani, Paneer Tikka, Chana Masala, Idli, Dosa, Masala Dosa, Sambar, Khichdi, Chicken Biryani, Poha, Upma, Naan, etc.
   - Every Indian record links to an official IFCT ID (e.g., `IFCT-A015`, `IFCT-B025`).
2. **USDA FoodData Central Foundation Assays:**
   - Authoritative source for international staples: Chicken Breast (raw/cooked), Whole Egg, Egg White, Atlantic Salmon, Tuna, Tofu, Milk, Curd/Dahi, Greek Yogurt, Brown/White Rice, Oats, Quinoa, Apple, Banana, Orange, Mango, Avocado, Spinach, Broccoli, Almonds, Walnuts, etc.
   - Every USDA record links to an official FDC ID (e.g., `FDC-171077`, `FDC-171287`).

### 6.2 Schema & Validation Fields
Each record contains:
- `id`: Unique normalized key
- `canonical_name`: Complete botanical / culinary title
- `aliases`: JSON array of vernacular and search synonyms
- `category`: Food category
- `default_portion_g`: Standard serving size in grams
- `portion_label`: User-facing portion description (e.g., "per medium roti (≈35g)")
- `calories`, `protein`, `carbohydrates`, `fat`, `sugar`, `fiber`, `sodium`, `cholesterol`, `saturated_fat`
- `source`: Documented laboratory authority
- `source_id`: Specific catalog identification code
- `verification_status`: `verified_standard` or `verified_lab`
