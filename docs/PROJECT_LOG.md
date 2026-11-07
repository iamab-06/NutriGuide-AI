# NutriGuide AI — Engineering Project Log

**Project Title:** NutriGuide AI: Multimodal Generative AI Food & Nutrition Intelligence  
**Institution:** Siddaganga Institute of Technology, Department of Computer Science & Engineering  
**Academic Target Deadline:** 30 October 2026  

---

## 1. Overview & Timeline

| Date | Phase | Focus |
|---|---|---|
| Oct 16, 2026 | Phase 1 & 2 | Scaffolding, Core UI Components, Page Architecture, Navigation |
| Oct 16, 2026 | Phase 3 | PyTorch MobileNetV3 Image Classifier, USDA FoodData Central integration, Open Food Facts API |
| Oct 16, 2026 | Phase 4 | Google Gemini 1.5 Flash GenAI integration, Evidence Grounding, FAISS + Sentence Transformers RAG |
| Oct 16, 2026 | Phase 5 | Automated Unit & Integration Testing, Benchmark Suite, Latency and Coverage Measurements |
| Oct 16, 2026 | Phase 6 | System Verification, End-to-End User Journey Validation, Academic Documentation Package |
| Oct 16, 2026 | Phase 7 | Classification Defect Audit, Transfer Learning Fine-Tuning (Food-101 20 classes), Gemini Vision Fallback |
| Oct 16, 2026 | Phase 8 | Food Identification Audit, Gemini Vision Samosa Verification, Strict Uncertainty Confirmation Policy (No Definitive Nutrition on Unconfirmed Food) |
| Oct 16, 2026 | Phase 9 | UI Polish & Academic Branding Removal (Removed watermark, notice banners, system status indicator) |
| Oct 16, 2026 | Phase 10 | Local LLM Migration: Migrated from Google Gemini to Local Google Gemma 3 4B IT (via Ollama) |

---

## 2. Inventory of Files Created & Enhanced

### Frontend (`frontend/src/`)
- `components/Layout.tsx`: Responsive navigation shell with dark forest-green sidebar (`#0d2818`), emerald active highlights (`#52b788`), mobile hamburger drawer, and system status indicator.
- `components/NutritionCard.tsx`: Reusable nutritional dashboard displaying per-100g macro/micronutrients with color coding, calorie highlight banner, USDA link, and missing-data fallbacks.
- `components/ConfidenceBadge.tsx`: Dynamic prediction confidence badge reflecting model certainty (green >=75%, blue <75%, yellow uncertain).
- `components/LoadingSpinner.tsx`: Branded animated status spinner.
- `components/ErrorMessage.tsx`: User-friendly error card with retry callback.
- `pages/Dashboard.tsx`: Comprehensive home dashboard with hero section, statistics cards, feature cards, and academic project disclaimers.
- `pages/AnalyzeFood.tsx`: Drag-and-drop food image classifier with preview, prediction confidence, top alternative candidate list with **one-click manual selection buttons**, **manual category correction dropdown (20 categories)**, **Gemini Vision multimodal fallback card with instant "Confirm & View Nutrition" button**, and **pending confirmation card withholding definitive nutrition until confirmed**.
- `pages/NutritionInfo.tsx`: Food search engine querying USDA FoodData Central with detailed nutrient breakdown.
- `pages/IngredientsAllergens.tsx`: Dual-mode lookup (by product name or barcode) accessing Open Food Facts with allergen highlighting and safety disclaimers.
- `pages/AIAssistant.tsx`: Interactive chat interface with conversation history, quick questions, and retrieved evidence provenance badges.
- `pages/CompareFoods.tsx`: Side-by-side per-100g nutritional comparison table with winner indicators, popular presets, and AI comparison summary.
- `services/api.ts`: Type-safe Axios client with global error normalization.
- `types/index.ts`: Shared TypeScript interfaces including `GeminiVisionFallback` and `requires_confirmation`.
- `vite.config.ts`: Vite 8 configuration with Tailwind CSS v4 and backend API reverse-proxy.

### Backend (`backend/app/`)
- `main.py`: FastAPI application with CORS middleware, lifespan event handlers, and modular router registrations.
- `core/config.py`: Centralized configuration loaded via `pydantic-settings` from `.env`, with `confidence_threshold = 0.70`.
- `core/categories.py`: Specification of 20 Food-101 target categories, human-readable display names, and mapped USDA search queries.
- `schemas/food.py`: Pydantic validation schemas for nutrition data, classification results (`confidence_threshold = 0.70`), product info, chat requests, comparisons, Gemini vision fallback, and `requires_confirmation`.
- `services/classifier.py`: PyTorch `MobileNetV3-Large` vision classifier with custom 20-class classification head, automated fine-tuned weight checkpoint loading (`nutriguide_classifier.pth`), top-5 prediction ranking, and `CONFIDENCE_THRESHOLD = 0.70` gating.
- `services/nutrition.py`: Async client for USDA FoodData Central with nutrient ID mapping for 9 core macro/micronutrients.
- `services/openfoodfacts.py`: Async integration with Open Food Facts API for packaged food ingredients, allergen tags, and barcode lookup with multi-host failover.
- `services/gemini_service.py`: Google Gemini client with structured evidence injection, multimodal vision fallback (`classify_food_with_gemini`), robust JSON parsing, and candidate model failover (`gemini-3.5-flash`, `gemini-3.5-flash-lite`, `gemini-3.1-flash-lite`, `gemini-flash-latest`, `gemini-3.8-flash`).
- `rag/rag_service.py`: Semantic retrieval system using Sentence Transformers (`all-MiniLM-L6-v2`) and FAISS vector index over 20 curated nutrition documents.
- `api/`: Modular routers for `/health`, `/categories`, `/analyze`, `/nutrition`, `/products`, `/chat`, and `/compare`.

### Machine Learning & Benchmarking Assets (`backend/`)
- `datasets/food20/`: Curated dataset with strict train/test split (15k train / 5k val, zero leakage).
- `models/nutriguide_classifier.pth`: Trained model checkpoint (17.1 MB, 90.64% Top-1, 97.82% Top-3).
- `models/baseline_eval_results.json`: Baseline empirical measurement log (2.60% Top-1).
- `models/training_log.json`: Training history across all 10 epochs.

### Testing & Verification (`backend/tests/`)
- `test_health.py`: Healthcheck and category count endpoints.
- `test_nutrition.py`: Nutrient ID extraction logic, search, and nutrition detail retrieval.
- `test_products.py`: Open Food Facts query and barcode parsing.
- `test_classifier.py`: Image preprocessing, inference, threshold enforcement, and input validation.
- `test_compare.py`: Pairwise food comparison and AI summary generation.
- `test_rag.py`: Knowledge base topic validation and retrieval interfaces.
- `test_gemini.py`: Configuration detection, secret masking, query entity extraction, context building, mocked chat, rate-limit resilience, schema contract, and live API inference.
- `test_vision_improvements.py`: Category integrity, prediction schema, real food inference, corrupted image rejection, and Gemini Vision fallback schema.
- `test_food_identification_fallback.py`: Comprehensive test module verifying:
  1. Correct local predictions above threshold with direct nutrition loading.
  2. Low-confidence predictions (< 70%, e.g., 43.9% samosa image) triggering Gemini Vision fallback.
  3. Strict withholding of definitive nutrition information for unconfirmed foods.
  4. Gemini Vision identifying a samosa from an image.
  5. Gemini Vision failure or unavailable credentials handling.
  6. User correction of an incorrect prediction via the nutrition endpoint.
- `benchmark.py`: Empirical measurement of classification latency (24.83 ms), entity matching accuracy (100%), uncertainty rejection, and RAG coverage.
- `verify_journeys.py`: End-to-end execution of all 5 user journeys through the Vite proxy.

---

## 3. Food Identification Audit & Fallback Resolution (Phase 8)

### 3.1 Problem Investigation & Pipeline Trace
- **Observed Behavior:** An image of a samosa was classified as Apple Pie with 43.9% confidence. The application displayed Apple Pie and retrieved Apple Pie nutrition. No separate Gemini Vision identification was visible.
- **Root Cause Identified:**
  1. `CONFIDENCE_THRESHOLD` was set to `0.40` (40%).
  2. Because $43.9\% \ge 40\%$, the local classifier evaluated `is_confident = True`.
  3. In `analyze.py`, the `if classification.is_confident:` branch was taken, which automatically called `get_nutrition_for_food("Apple Pie")`.
  4. The `else` block (which triggers `classify_food_with_gemini`) was completely bypassed.
  5. Furthermore, when Gemini Vision was called previously, the backend had been automatically retrieving nutrition for Gemini's suggestion rather than presenting it as an unconfirmed suggestion for the user to confirm.

### 3.2 Implemented Architectural Fixes
1. **Calibrated Confidence Threshold (70%):**
   - Configured `confidence_threshold: float = 0.70` in `config.py` and `classifier.py`.
   - Clear, unambiguous predictions ($\ge 70\%$, such as Chocolate Cake 100%, Chicken Curry 100%, clear Samosa 100%) are accepted directly.
   - Ambiguous or moderate-confidence predictions ($< 70\%$, such as the 43.9% Apple Pie prediction on a samosa) are flagged as `is_confident = False` and `requires_confirmation = True`.
2. **Automatic Gemini Vision Fallback Invocation:**
   - Any prediction below 70% automatically triggers `classify_food_with_gemini(image_bytes)`.
   - Gemini Vision analyzes the image, identifies the dish (e.g. "Samosa", "golden-brown, triangular pastry with crisp, fried crust"), and returns confidence and category match.
3. **Strict Nutrition Withholding Policy for Unconfirmed Food:**
   - When identification is uncertain, `nutrition = None`.
   - Definitive nutrition information is **withheld** until the user confirms the food identity, preventing false dietary advice.
4. **Interactive Confirmation & Correction UI (`AnalyzeFood.tsx`):**
   - The Gemini Vision card presents an action button: `"Confirm [Suggested Food] & View Nutrition"`.
   - Clicking this button immediately calls `handleSelectAlternative`, updates the confirmed food, and fetches verified USDA nutrition.
   - The alternative predictions list provides `"Select"` buttons on each candidate.
   - The manual category dropdown allows instant override to any of the 20 supported foods.
   - While unconfirmed, an informative card is displayed: `"Nutritional Data Pending Confirmation. To ensure accuracy and prevent false dietary claims, definitive nutritional facts are only retrieved after you confirm the food item above."`

---

## 4. Verification Summary

- **`pytest -v`:** **37 / 37 passed (100% pass rate)** in 80.46s.
- **`tsc -b && vite build`:** Production bundle built in 1.75s (0 errors).
- **`tests/benchmark.py`:** Avg latency 24.83 ms, 100% entity coverage, 100% uncertainty rejection compliance.
- **`tests/verify_journeys.py`:** All 5 user journeys passed end-to-end through the Vite proxy.

---

## 5. Dashboard UI & Layout Polish (Phase 9)

### 5.1 Objectives & Design Principles
- Refined dashboard and shared application layout to achieve a cleaner, professional, and visually consistent appearance in strict alignment with the approved forest-green-and-white theme (`#0d2818`, `#2d6a4f`, `#52b788`).
- Eliminated unnecessary branding and visual clutter without modifying backend functionality or breaking responsive navigation.

### 5.2 Implemented Refinements
1. **Unnecessary Branding & Indicators Removed (`Layout.tsx`):**
   - Removed the `"NutriGuide AI • SIT CSE 2026"` sidebar footer text block.
   - Removed the `"System Active"` green pulse indicator block from the top header bar.
   - Kept the header clean and focused with the mobile navigation trigger and active route title.
2. **Simplified Dashboard Statistics Cards (`Dashboard.tsx`):**
   - Removed decorative icons (`Leaf`, `Zap`, `TrendingUp`) from the statistics cards.
   - Restyled cards with crisp high-contrast typography (`text-3xl font-bold tracking-tight`), uppercase tracking labels (`text-xs font-semibold text-gray-500 uppercase tracking-wider`), and restrained emerald subtext badges (`bg-[#e8f4ed] text-[#2d6a4f]`).
   - Configured responsive grid (`grid-cols-1 sm:grid-cols-3`) with subtle borders and hover micro-interactions.
3. **Refined Feature Cards (`Dashboard.tsx`):**
   - Eliminated mismatched multi-color rainbow gradients (`blue-500`, `orange-500`, `purple-500`, `teal-500`) and pastel box backgrounds.
   - Harmonized all 5 feature cards to use the brand design language: unified emerald icon container (`bg-[#e8f4ed] text-[#2d6a4f]`) that transitions to dark green (`bg-[#2d6a4f] text-white`) on hover.
   - Added subtle action indicators (`Explore feature →`) and responsive borders (`hover:border-[#52b788]/50`).
   - Preserved all 5 feature destinations:
     - Food Recognition (`/analyze`)
     - Nutrition Analysis (`/nutrition`)
     - Allergen Awareness (`/ingredients`)
     - AI Nutrition Assistant (`/assistant`)
     - Food Comparison (`/compare`)
4. **Preserved Backend & Functional Integrity:**
   - 0 changes made to backend APIs, ML models, USDA integration, Open Food Facts service, or RAG pipeline.
   - Frontend production build (`tsc -b && vite build`) passed with 0 errors in 1.75s.

---

## 6. Academic Notice Banner Removal & Live USDA API Verification (Phase 10)

### 6.1 Academic Notice Banner Removal
- Located the notice banner block in `frontend/src/pages/Dashboard.tsx`.
- Removed the entire disclaimer banner (`Academic Project Notice: NutriGuide AI is a Computer Science academic project built at Siddaganga Institute of Technology...`).
- Preserved all surrounding dashboard feature cards, hero section, statistics, and theme styling without adding replacement messages.

### 6.2 USDA API Configuration & Security Verification
- **Environment & Git Hygiene:** Confirmed `backend/.env` is tracked as ignored by Git (`git check-ignore backend/.env`).
- **Configuration Loading:** Confirmed `backend/.env` defines `USDA_API_KEY` (40-character key), accurately mapped to `settings.usda_api_key`.
- **Secret Masking:** Enhanced `Settings.__repr__` in `backend/app/core/config.py` to mask `usda_api_key` (`***`) and prevent inadvertent secret exposure in logs.
- **Error Sanitization:** Sanitized exception logging in `backend/app/services/nutrition.py` to log exception types rather than full HTTP exception instances that could contain query strings.
- **Source Attribution:** Refined `get_nutrition_for_food` to dynamically tag live USDA results (`"USDA FoodData Central"`) vs offline fallback reference entries (`"USDA FoodData Central (Standard Reference)"`).
- **Process Reload:** Restarted the Uvicorn background service to reload the updated environment variables.

### 6.3 Test & Verification Results
- **Live USDA API Verification:**
  - Query: `"pizza"`.
  - Returned 10 live USDA records with real FDC IDs (`172041: PIZZA HUT 12" Cheese Pizza, Pan Crust`, Fast Foods).
  - Detailed nutrition retrieved: `280.0 kcal`, `11.73g protein`, `29.93g carbs`, `12.56g fat` per 100g.
  - Source attribution: `"USDA FoodData Central"` (Live API confirmed; fallback was NOT invoked).
  - Vite proxy route `/api/nutrition/search?q=pizza` also returned 10 live results with HTTP 200.
- **Backend Test Suite:** `pytest -v` executed **37 / 37 passed (100% pass rate)** in 71.18s.
- **Frontend Production Build:** `npm run build` (`tsc -b && vite build`) passed with **0 errors in 1.75s**.

---

## 7. Ingredients & Allergens Top Notice Removal (Phase 11)
- Located top amber notice banner in `frontend/src/pages/IngredientsAllergens.tsx` (`Important: Allergen information is sourced from Open Food Facts community database...`).
- Removed the entire banner without altering search tabs, form inputs, or product card allergen displays.
- Frontend production build (`npm run build`) passed with **0 errors in 1.22s**.

---

## 8. AI Nutrition Assistant Header Polish (Phase 12)
- Cleaned up the header in `frontend/src/pages/AIAssistant.tsx`.
- Removed three elements completely:
  1. Subtitle: `Powered by Gemini + RAG knowledge base`.
  2. Bot logo container to the left of the title.
  3. `Evidence-grounded` label badge on the right.
- Preserved the clean `AI Nutrition Assistant` heading with consistent layout spacing, border, and theme alignment.
- Removed unused `Bot` and `BookOpen` icon imports.
- Frontend production build (`npm run build`) passed with **0 errors in 1.20s**.

---

## 9. Migration to Local Gemma 3 4B IT via Ollama (Phase 13)

### 9.1 Objectives & Motivation
- Replaced remote Google Gemini cloud API with local **Google Gemma 3 4B IT** (`gemma3:4b`) running via **Ollama**.
- Eliminated remote API rate-limit bottlenecks (`ResourceExhausted` 429), recurring cloud latency, and token billing.
- Preserved complete user privacy: images and queries are processed entirely on-device without cloud transmission.

### 9.2 Implementation Details
1. **New Local LLM Service (`backend/app/services/ollama_service.py`):**
   - Multimodal vision fallback: `classify_food_with_vision(image_bytes)` with JPEG base64 encoding and structured JSON parsing.
   - Grounded conversational assistant: `chat_with_context(user_message, food_context, history)` with strict system instructions and evidence injection.
   - Dietary concept analysis: `explain_nutrition(food_name, nutrition_data)`.
   - Health and availability checks: `check_ollama_health()` and `is_ollama_configured()`.
   - Non-blocking asynchronous HTTP execution via `httpx.AsyncClient` with split connection timeout (`connect=5.0s`, `total=120s`).
2. **Configuration Updates (`backend/app/core/config.py`):**
   - Added `ollama_base_url: str = "http://localhost:11434"`.
   - Added `ollama_model: str = "gemma3:4b"`.
   - Added `ollama_timeout: int = 120`.
   - Kept `gemini_api_key` optional for backwards compatibility.
3. **API Router Integration:**
   - `backend/app/api/analyze.py`: Switched to `classify_food_with_vision` for predictions under the 70% threshold.
   - `backend/app/api/chat.py`: Switched to Ollama `chat_with_context`.
   - `backend/app/api/compare.py`: Switched to Ollama `chat_with_context`.
   - Preserved all response schemas (`AnalyzeImageResponse`, `ChatResponse`, `CompareResponse`).
4. **Frontend Theme & Label Consistency:**
   - `frontend/src/pages/AIAssistant.tsx`: Updated welcome greeting to reference local Gemma 3 4B IT.
   - `frontend/src/pages/AnalyzeFood.tsx`: Updated vision fallback badges and labels to Gemma 3 Vision.
   - `frontend/src/pages/CompareFoods.tsx`: Updated comparison summary attribution to Gemma 3 4B.
   - `frontend/src/pages/Dashboard.tsx`: Updated model stat badge and description to Gemma 3 4B.
5. **Testing & Verification Suite:**
   - Created `backend/tests/test_ollama.py` with 14 unit and integration tests covering configuration, health checks, mocked chat, vision analysis, error handling (offline and timeout), and endpoint schemas.
   - Updated `test_food_identification_fallback.py`, `test_vision_improvements.py`, and `verify_end_to_end.py`.
   - Resolved relative weights path resolution in `classifier.py` for execution across working directories.
6. **Documentation & Deployment Guides:**
   - Updated `README.md`, `SETUP_AND_EXECUTION_GUIDE.md`, `SYSTEM_ARCHITECTURE.md`, `TECHNOLOGY_STACK.md`, `AI_AND_RAG_PIPELINE.md`, and `DEVELOPMENT_CHALLENGES.md`.

### 9.3 Verification Results
- **Full Backend Pytest Suite:** **51 / 51 passed (100%) in 61.23s**.
- **Frontend Production Build:** `npm run build` completed with **0 errors in 2.19s** (381.45 kB bundle, 121.02 kB gzip).

---

## 10. Phase 15: General Nutrition Science Knowledge Grounding & Straightforward Assistant Answers (November 2026)

### 10.1 Problem Statement & Objectives
- **Problem:** AI Assistant was giving evasive responses (e.g., *"nutrition data is not provided in your knowledge base"*) when asked real-world comparative dietary questions outside the original 20 Food-101 dishes (such as *"which is high in protein 250gms chicken breast or 10 whole eggs?"*).
- **Objectives:**
  1. Eliminate evasive non-answers by removing rigid missing-data refusal directives.
  2. Expand food grounding beyond 20 categories to general staples (chicken breast, eggs, salmon, tofu, oats, banana, etc.) and arbitrary foods via live USDA API lookup.
  3. Ensure the assistant provides direct, authoritative answers in the first sentence with clear step-by-step arithmetic for user portions.
  4. Maintain fast local GPU inference (< 18s on NVIDIA RTX 3050 Laptop GPU).

### 10.2 Implementation
1. **Multi-Entity Food Extraction & Reference Matching (`backend/app/api/chat.py`):**
   - Implemented `_extract_candidate_food_terms(text)` to extract plural/singular food tokens and multi-word phrases.
   - Implemented `_match_reference_food(term)` with prefix and modifier stripping (raw, cooked, whole, etc.) for instant 0ms in-memory lookup.
   - Added asynchronous fallback to `get_nutrition_for_food` with a 3.0s timeout to dynamically retrieve unindexed foods from live USDA FoodData Central.
   - Added deterministic portion and unit scaling (`_parse_quantities_from_query` & `_scale_nutrition_to_quantity`): extracts user-specified gram amounts or unit counts (e.g., 300g chicken breast, 10 eggs), calculates exact scaled macronutrients in Python, and injects pre-calculated figures labeled with `★ Calculation verified by backend`.
2. **Standard Reference Data Expansion (`backend/app/core/categories.py`):**
   - Added standard per-100g USDA reference figures for staple foods (`chicken_breast`, `egg`, `salmon`, `tofu`, `banana`, `oats`, `greek_yogurt`).
3. **Upgraded System Prompt Architecture (`backend/app/services/ollama_service.py`):**
   - Rule 1: State direct answer/winner in the very first sentence.
   - Rule 2: Explicit instruction to use pre-calculated backend arithmetic as-is without re-multiplying or hallucinating mental math.
   - Rule 3: Use verified context if provided; otherwise seamlessly use standard USDA averages instead of refusing.
   - Rule 4: Maximum 150 words to minimize generation latency.

### 10.3 Verification Results
- **Direct Answer Verification:**
  - Query: *"which gives me a good quality protein 300gms raw chicken breast or 10 whole eggs?"*
  - Response: *"300 grams of raw chicken breast provides a significantly higher quality protein source than 10 whole eggs. 300 grams of cooked chicken breast provides 93.0 grams of protein, while 10 large whole eggs provide 63.0 grams of protein... Breakdown: Chicken Breast (300g): Protein: 93.0 g | Eggs (10 whole): Protein: 63.0 g"* (Delivered in 14.8s).
- **Pytest Suite:** 51 / 51 tests passed (100%).
- **Frontend Production Build:** `npm run build` completed with 0 errors in 1.81s.
