# NutriGuide AI — RESTful API Documentation

**Application:** NutriGuide AI  
**Base URL:** `http://localhost:8000` (or `/api` via Vite dev proxy)  
**Protocol:** HTTP/1.1 REST  
**Data Exchange Format:** `application/json` (or `multipart/form-data` for image upload)  

---

## 1. System Health & Catalog Endpoints

### 1.1 Health Check
- **Endpoint:** `GET /api/health`
- **Purpose:** Verifies backend liveness, application name, and version.
- **Request Parameters:** None.
- **Response Headers:** `Content-Type: application/json`
- **Status Codes:** `200 OK`
- **Example Response:**
  ```json
  {
    "status": "ok",
    "app": "NutriGuide AI",
    "version": "1.0.0"
  }
  ```

### 1.2 Categories Catalog
- **Endpoint:** `GET /api/categories`
- **Purpose:** Returns the complete list of 20 AI-recognized Food-101 categories with human-readable display names and USDA search query mappings.
- **Request Parameters:** None.
- **Status Codes:** `200 OK`
- **Example Response:**
  ```json
  {
    "total": 20,
    "categories": [
      {
        "key": "apple_pie",
        "display_name": "Apple Pie",
        "usda_query": "apple pie"
      },
      {
        "key": "pizza",
        "display_name": "Pizza",
        "usda_query": "cheese pizza, regular crust"
      },
      {
        "key": "samosa",
        "display_name": "Samosa",
        "usda_query": "samosa"
      }
    ]
  }
  ```

---

## 2. Food Image Analysis Endpoint

### 2.1 Analyze Food Image
- **Endpoint:** `POST /api/analyze`
- **Purpose:** Uploads a food photograph, runs fine-tuned MobileNetV3-Large classification, checks the 70% confidence threshold, triggers Gemini Vision fallback when uncertain, and returns structured predictions.
- **Content-Type:** `multipart/form-data`
- **Request Body:**
  | Field | Type | Required | Description |
  |---|---|---|---|
  | `file` | `UploadFile` (Binary) | Yes | Image file (JPEG, PNG, WebP $\le 10\text{ MB}$) |
- **Status Codes:**
  - `200 OK`: Successful inference.
  - `400 Bad Request`: Non-image file uploaded or corrupted image payload.

#### Example Response A: High-Confidence Prediction ($\ge 70\%$)
```json
{
  "classification": {
    "predicted_class": "pizza",
    "display_name": "Pizza",
    "confidence": 0.942,
    "top_predictions": [
      {
        "class": "pizza",
        "display_name": "Pizza",
        "confidence": 0.942,
        "confidence_pct": "94.2%"
      },
      {
        "class": "omelette",
        "display_name": "Omelette",
        "confidence": 0.024,
        "confidence_pct": "2.4%"
      }
    ],
    "is_confident": true,
    "confidence_threshold": 0.70,
    "model_version": "MobileNetV3-NutriGuide-v1",
    "supported_categories": ["Apple Pie", "Caesar Salad", "Pizza", "Samosa", "..."]
  },
  "nutrition": {
    "food_name": "Cheese pizza, regular crust",
    "source": "USDA FoodData Central",
    "fdcId": 173292,
    "basis": "per 100g",
    "calories": 266.0,
    "protein": 10.5,
    "carbohydrates": 33.0,
    "fat": 10.0,
    "sugar": 3.8,
    "fiber": 2.3,
    "sodium": 598.0,
    "cholesterol": 17.0,
    "saturated_fat": 4.5,
    "data_available": true
  },
  "message": "Food identified successfully.",
  "gemini_fallback": null,
  "requires_confirmation": false
}
```

#### Example Response B: Uncertain Prediction ($< 70\%$, e.g., Ambiguous Samosa)
```json
{
  "classification": {
    "predicted_class": "apple_pie",
    "display_name": "Apple Pie",
    "confidence": 0.439,
    "top_predictions": [
      {
        "class": "apple_pie",
        "display_name": "Apple Pie",
        "confidence": 0.439,
        "confidence_pct": "43.9%"
      },
      {
        "class": "samosa",
        "display_name": "Samosa",
        "confidence": 0.312,
        "confidence_pct": "31.2%"
      }
    ],
    "is_confident": false,
    "confidence_threshold": 0.70,
    "model_version": "MobileNetV3-NutriGuide-v1"
  },
  "nutrition": null,
  "message": "Identification uncertain (43.9% confidence). Nutritional data is withheld pending user confirmation.",
  "gemini_fallback": {
    "suggested_food": "Samosa",
    "confidence": "High",
    "explanation": "Image displays a golden-brown triangular fried pastry characteristic of a samosa.",
    "category_match": "samosa"
  },
  "requires_confirmation": true
}
```

---

## 3. Nutrition Information Endpoints

### 3.1 Search Foods in USDA FoodData Central
- **Endpoint:** `GET /api/nutrition/search`
- **Parameters:**
  | Parameter | Type | Required | Default | Description |
  |---|---|---|---|---|
  | `q` | `string` | Yes | — | Search term (min length: 2 chars) |
- **Example Response:**
  ```json
  {
    "results": [
      {
        "fdcId": 172041,
        "description": "PIZZA HUT 12\" Cheese Pizza, Pan Crust",
        "food_category": "Fast Foods",
        "brand_owner": null,
        "score": 100.0
      }
    ]
  }
  ```

### 3.2 Retrieve Nutrition by Food Name
- **Endpoint:** `GET /api/nutrition/{food_name}`
- **Parameters:**
  | Parameter | Location | Type | Required | Description |
  |---|---|---|---|---|
  | `food_name` | Path | `string` | Yes | Name of the food item |
  | `category_key` | Query | `string` | Optional | Internal category key for optimal matching |
- **Example Response:**
  ```json
  {
    "food_name": "PIZZA HUT 12\" Cheese Pizza, Pan Crust",
    "source": "USDA FoodData Central",
    "fdcId": 172041,
    "basis": "per 100g",
    "calories": 280.0,
    "protein": 11.73,
    "carbohydrates": 29.93,
    "fat": 12.56,
    "sugar": 3.42,
    "fiber": 2.1,
    "sodium": 594.0,
    "cholesterol": 24.0,
    "saturated_fat": 5.48,
    "nutrients": [
      { "name": "Calories", "amount": 280.0, "unit": "kcal" },
      { "name": "Protein", "amount": 11.73, "unit": "g" }
    ],
    "data_available": true
  }
  ```

---

## 4. Packaged Products Endpoints (Open Food Facts)

### 4.1 Search Products by Name
- **Endpoint:** `GET /api/products/search`
- **Parameters:**
  | Parameter | Type | Required | Default | Description |
  |---|---|---|---|---|
  | `q` | `string` | Yes | — | Product search query (e.g., "Nutella") |
  | `page_size`| `int` | Optional | `5` | Maximum products to return |
- **Example Response:**
  ```json
  {
    "results": [
      {
        "product_name": "Nutella",
        "brands": "Ferrero",
        "ingredients_text": "Sugar, palm oil, hazelnuts (13%), skimmed milk powder (8.7%), fat-reduced cocoa (7.4%), emulsifier: lecithins (soya), vanillin.",
        "allergens": "en:milk,en:nuts,en:soybeans",
        "allergens_tags": ["en:milk", "en:nuts", "en:soybeans"],
        "barcode": "3017620422003",
        "source": "Open Food Facts",
        "data_complete": true,
        "missing_fields": []
      }
    ]
  }
  ```

### 4.2 Lookup Product by Barcode
- **Endpoint:** `GET /api/products/barcode/{barcode}`
- **Parameters:**
  | Parameter | Location | Type | Required | Description |
  |---|---|---|---|---|
  | `barcode` | Path | `string` | Yes | EAN-13, EAN-8, or UPC-A barcode number |
- **Status Codes:** `200 OK`, `404 Not Found`

---

## 5. Conversational AI Assistant & Food Comparison

### 5.1 Chat with AI Assistant
- **Endpoint:** `POST /api/chat`
- **Request Body:**
  ```json
  {
    "message": "What are the macronutrients of fried rice?",
    "food_context": null,
    "history": []
  }
  ```
- **Example Response:**
  ```json
  {
    "answer": "Based on verified USDA FoodData Central records, 100g of fried rice provides approximately 163 kcal, 5.2g of protein, 28.0g of carbohydrates, and 3.5g of total fat. It is a carbohydrate-dense dish...",
    "sources": ["USDA FoodData Central", "NutriGuide Knowledge Base"],
    "evidence_used": true,
    "warning": null
  }
  ```

### 5.2 Compare Two Foods
- **Endpoint:** `POST /api/compare`
- **Request Body:**
  ```json
  {
    "food1": "pizza",
    "food2": "hamburger"
  }
  ```
- **Example Response:**
  ```json
  {
    "food1": {
      "food_name": "Cheese pizza, regular crust",
      "calories": 266.0,
      "protein": 10.5,
      "carbohydrates": 33.0,
      "fat": 10.0,
      "basis": "per 100g"
    },
    "food2": {
      "food_name": "Hamburger, single patty",
      "calories": 254.0,
      "protein": 13.0,
      "carbohydrates": 24.0,
      "fat": 11.5,
      "basis": "per 100g"
    },
    "basis": "per 100g",
    "comparison_notes": "Normalized per 100g. Values from USDA FoodData Central.",
    "ai_summary": "Per 100g, the hamburger provides higher protein density (13.0g vs 10.5g) and fewer carbohydrates (24.0g vs 33.0g), while pizza has slightly higher calories..."
  }
  ```
