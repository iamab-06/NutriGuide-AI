# NutriGuide AI — Classroom & Viva Project Demo Guide

**Project:** NutriGuide AI: Multimodal Food Recognition and Nutrition Analysis Assistant  
**Institution:** Department of Computer Science and Engineering, Siddaganga Institute of Technology  
**Academic Target:** Live Evaluation, Classroom Demo & External Viva Defense (2026)  

---

## 1. Pre-Demo Preparation Checklist

Before the committee enters or the presentation begins, verify the following steps:

- [ ] Python virtual environment is activated.
- [ ] Dependencies installed (`pip list` includes `fastapi`, `torch`, `torchvision`, `google-generativeai`, `sentence-transformers`, `faiss-cpu`).
- [ ] `backend/.env` file exists and contains valid keys for `GEMINI_API_KEY` and `USDA_API_KEY`.
- [ ] PyTorch checkpoint exists at `backend/models/nutriguide_classifier.pth` (17.1 MB).
- [ ] Node dependencies installed (`npm list` in `frontend/` succeeds).
- [ ] Port 8000 (FastAPI) and Port 5173 (Vite) are free and available.
- [ ] Sample test images ready in a convenient demonstration folder (e.g., Pizza, Samosa, Caesar Salad, Hamburger).

---

## 2. Startup Sequence (Two Terminal Windows)

### Terminal 1: Backend Server (FastAPI + Uvicorn)
```powershell
cd "c:\NutriGuide Ai\backend"
# If using virtual environment:
# .\venv\Scripts\Activate.ps1
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
**Expected Terminal Output:**
```text
INFO:     Started server process [PID]
INFO:     Waiting for application startup.
INFO:     Loaded fine-tuned weights from models/nutriguide_classifier.pth
INFO:     RAG pipeline initialized: 20 documents indexed in FAISS L2.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

### Terminal 2: Frontend Development Server (Vite 8)
```powershell
cd "c:\NutriGuide Ai\frontend"
npm run dev
```
**Expected Terminal Output:**
```text
  VITE v8.3.4  ready in 320 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

Open your browser to: **`http://localhost:5173`**

---

## 3. Step-by-Step Live Demonstration Script

### Demo Scenario 1: The Modern Clean Dashboard
- **Navigation:** Click on `Dashboard` in the sidebar (`/`).
- **Talking Points:**
  - Point out the clean forest-green and white design system (`#0d2818`, `#2d6a4f`, `#52b788`).
  - Highlight the 3 key metric cards: **20 Food Categories** (MobileNetV3), **USDA Data Source** (FoodData Central), and **Gemini + RAG Pipeline**.
  - Show the 5 quick action cards for direct feature navigation.

---

### Demo Scenario 2: High-Confidence Food Recognition (The Pizza Test)
- **Navigation:** Click on `Analyze Food` in the sidebar (`/analyze`).
- **Action:** Drag and drop or browse to select a clear photo of a **Pizza**.
- **Observation:**
  - Spinner displays: *"Analyzing image... Classifying food and retrieving nutrition data..."*
  - Within ~350 ms, the image preview renders.
  - The prediction badge displays **Pizza** with a green **Confidence Badge ($\ge 75\%$)**.
  - The **`NutritionCard`** appears immediately, populated with verified per-100g USDA data:
    - Calories: `~266 kcal` (Orange callout box)
    - Protein: `10.5 g`
    - Carbohydrates: `33.0 g`
    - Total Fat: `10.0 g`
    - Dietary Fiber: `2.3 g`
    - Direct hyperlink to official USDA FDC entry.
- **Talking Points:** Explain that because confidence exceeded the 70% threshold, the system securely verified the dish and pulled authoritative data without requiring manual intervention.

---

### Demo Scenario 3: Ambiguous Recognition & Gemini Vision Fallback (The Samosa Test)
- **Navigation:** Click *"Analyze Another Image"* on `/analyze`.
- **Action:** Upload a challenging, angled, or low-contrast photo of a **Samosa** (or a food with visual similarity to pastries).
- **Observation:**
  - Local MobileNetV3 outputs a moderate or ambiguous confidence score ($< 70\%$, e.g. 43.9%).
  - **Notice the Safety Protocol:** The `NutritionCard` is **NOT** displayed!
  - Instead, an amber card alerts: *"Nutritional Data Pending Confirmation. To ensure accuracy, definitive nutritional facts are only retrieved after you confirm the food item."*
  - The **Gemini Vision Fallback Card** appears, displaying:
    - *"Suggested Food: Samosa"*
    - *"Visual Explanation: Triangular pastry with golden-brown fried crust and spiced vegetable filling."*
    - A prominent action button: **`Confirm Samosa & View Nutrition`**.
  - Top alternative candidate chips appear with `"Select"` buttons.
  - A manual 20-category dropdown is available as an override.
- **Action:** Click the button **`Confirm Samosa & View Nutrition`**.
- **Observation:**
  - State instantly transitions to confirmed.
  - Verified USDA nutritional breakdown for Samosa (262 kcal, 4.4g protein, 32.2g carbs, 13g fat) renders dynamically!
- **Talking Points:** Emphasize to the committee that NutriGuide AI is the only academic system that does not force false predictions—it combines local edge AI with multimodal cloud fallback and user-in-the-loop confirmation.

---

### Demo Scenario 4: Authoritative USDA Nutrition Search
- **Navigation:** Click `Nutrition Info` in the sidebar (`/nutrition`).
- **Action:** In the search input, type **`chicken curry`** and click Search.
- **Observation:**
  - Search results display official USDA Foundation and SR Legacy matching records with FDC IDs.
  - Click on the first result (`Chicken curry`).
  - Full nutritional profile opens showing all 9 core nutrients per 100g.
- **Talking Points:** Point out that all data is normalized per 100g, allowing direct scientific comparison regardless of recipe serving size.

---

### Demo Scenario 5: Packaged Products & Allergen Awareness (Open Food Facts)
- **Navigation:** Click `Ingredients & Allergens` in the sidebar (`/ingredients`).
- **Action A (Search by Name):** Type **`Nutella`** and click Search.
  - Result displays product image, brand owner (Ferrero), ingredient text, and bold red allergen badges: `milk`, `nuts`, `soybeans`.
- **Action B (Lookup by Barcode):** Switch tab to *Search by Barcode*, enter **`3017620422003`**, and click Lookup.
  - Instantly retrieves the exact physical product record from Open Food Facts.
- **Action C (Allergen Disclaimer):** Show products with no declared allergens, highlighting the defensive notice: *"No allergens declared in database. This does NOT confirm the product is allergen-free."*

---

### Demo Scenario 6: Evidence-Grounded Conversational AI Assistant
- **Navigation:** Click `AI Assistant` in the sidebar (`/assistant`).
- **Action A:** Click the quick prompt: *"What makes chicken curry nutritious?"*
  - Assistant responds with evidence-grounded nutritional analysis.
  - Provenance badges display: `USDA FoodData Central` and `NutriGuide Knowledge Base`.
- **Action B:** Ask a specific macro question: *"What are the exact macros of fried rice per 100g?"*
  - Auto-grounding kicks in: the model states exactly 163 kcal, 5.2g protein, 28g carbs, 3.5g fat based on verified USDA records without hallucinating numbers.

---

### Demo Scenario 7: Objective Side-by-Side Food Comparison
- **Navigation:** Click `Compare Foods` in the sidebar (`/compare`).
- **Action:** Enter Food 1: **`pizza`** and Food 2: **`hamburger`** and click Compare.
- **Observation:**
  - Comparative nutritional table displays both items normalized per 100g side-by-side.
  - Superiority indicators highlight advantageous macronutrients (e.g. Hamburger has higher protein density at 13.0g vs 10.5g).
  - Gemini AI provides an objective dietary synthesis explaining the balance between protein density and saturated fat without biased declarations.

---

## 4. Troubleshooting & Fallback Demonstration

| Issue / Failure Mode | Root Cause | System Response / Fix |
|---|---|---|
| **Gemini API Key missing or quota exceeded** | Network block or 429 quota | System automatically falls back to local knowledge base and serves factual USDA data with service notice. |
| **USDA API rate limits or timeout** | High burst requests | System automatically queries local verified `USDA_REFERENCE_DATA` and updates source attribution to `Standard Reference`. |
| **Corrupted or non-food image uploaded** | Invalid payload | Ingestion returns clean HTTP 400 Bad Request; UI displays friendly error card with retry button. |
