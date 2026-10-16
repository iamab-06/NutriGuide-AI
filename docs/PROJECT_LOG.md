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

---

## 2. Inventory of Files Created

### Frontend (`frontend/src/`)
- `components/Layout.tsx`: Responsive navigation shell with dark forest-green sidebar (`#0d2818`), emerald active highlights (`#52b788`), mobile hamburger drawer, and system status indicator.
- `components/NutritionCard.tsx`: Reusable nutritional dashboard displaying per-100g macro/micronutrients with color coding, calorie highlight banner, USDA link, and missing-data fallbacks.
- `components/ConfidenceBadge.tsx`: Dynamic prediction confidence badge reflecting model certainty (green >=75%, blue <75%, yellow uncertain).
- `components/LoadingSpinner.tsx`: Branded animated status spinner.
- `components/ErrorMessage.tsx`: User-friendly error card with retry callback.
- `pages/Dashboard.tsx`: Comprehensive home dashboard with hero section, statistics cards, feature cards, and academic project disclaimers.
- `pages/AnalyzeFood.tsx`: Drag-and-drop food image classifier with preview, prediction confidence, top alternative candidate list, and linked nutrition details.
- `pages/NutritionInfo.tsx`: Food search engine querying USDA FoodData Central with detailed nutrient breakdown.
- `pages/IngredientsAllergens.tsx`: Dual-mode lookup (by product name or barcode) accessing Open Food Facts with allergen highlighting and safety disclaimers.
- `pages/AIAssistant.tsx`: Interactive chat interface with conversation history, quick questions, and retrieved evidence provenance badges.
- `pages/CompareFoods.tsx`: Side-by-side per-100g nutritional comparison table with winner indicators, popular presets, and AI comparison summary.
- `services/api.ts`: Type-safe Axios client with global error normalization.
- `types/index.ts`: Shared TypeScript interfaces.
- `vite.config.ts`: Vite 8 configuration with Tailwind CSS v4 and backend API reverse-proxy.

### Backend (`backend/app/`)
- `main.py`: FastAPI application with CORS middleware, lifespan event handlers, and modular router registrations.
- `core/config.py`: Centralized configuration loaded via `pydantic-settings` from `.env`.
- `core/categories.py`: Specification of 20 Food-101 target categories, human-readable display names, and mapped USDA search queries.
- `schemas/food.py`: Pydantic validation schemas for nutrition data, classification results, product info, chat requests, and comparisons.
- `services/classifier.py`: PyTorch `MobileNetV3-Large` vision classifier supporting top-5 probability ranking and 40% confidence threshold gating.
- `services/nutrition.py`: Async client for USDA FoodData Central with nutrient ID mapping for 9 core macro/micronutrients.
- `services/openfoodfacts.py`: Async integration with Open Food Facts API for packaged food ingredients, allergen tags, and barcode lookup.
- `services/gemini_service.py`: Google Gemini 1.5 Flash client with structured evidence injection preventing ungrounded claims.
- `rag/rag_service.py`: Semantic retrieval system using Sentence Transformers (`all-MiniLM-L6-v2`) and FAISS vector index over 20 curated nutrition documents.
- `api/`: Modular routers for `/health`, `/categories`, `/analyze`, `/nutrition`, `/products`, `/chat`, and `/compare`.

### Testing & Verification (`backend/tests/`)
- `test_health.py`: Healthcheck and category count endpoints.
- `test_nutrition.py`: Nutrient ID extraction logic, search, and nutrition detail retrieval.
- `test_products.py`: Open Food Facts query and barcode parsing.
- `test_classifier.py`: Image preprocessing, inference, threshold enforcement, and input validation.
- `test_compare.py`: Pairwise food comparison and AI summary generation.
- `test_rag.py`: Knowledge base topic validation and retrieval interfaces.
- `benchmark.py`: Empirical measurement of classification latency, entity matching accuracy, uncertainty rejection, and RAG coverage.
- `verify_end_to_end.py`: End-to-end execution of all 6 user journeys (A through F).

---

## 3. Key Implementation Decisions & Technical Rationale

1. **MobileNetV3-Large for Computer Vision:**
   - *Rationale:* Selected for optimal trade-off between parameter efficiency and accuracy. Highly suitable for edge and CPU inference, achieving ~25ms inference latency without requiring dedicated GPU server instances.
2. **Confidence Thresholding (40% Cutoff):**
   - *Rationale:* Prevents hallucinated or forced food classifications on non-food or out-of-domain images. When confidence is below 0.40, the system displays an explicit warning and prompts the user to confirm or search manually.
3. **Per-100g Standardized Nutritional Basis:**
   - *Rationale:* Packaged foods and recipes vary widely in serving sizes. Enforcing a 100g measurement basis ensures honest, mathematically sound comparisons across different foods.
4. **Structured Evidence Injection for LLM Prompts:**
   - *Rationale:* Gemini 1.5 Flash is prohibited from guessing numerical nutrient values. The prompt injects verified USDA numbers as authoritative ground truth, instructing the model to cite absence when data is missing.
5. **Community Allergen Disclaimer Policy:**
   - *Rationale:* In Open Food Facts, an empty allergen field does not prove an item is allergen-free. The UI explicitly alerts users that absence of declared allergens does not constitute clinical safety.

---

## 4. Bugs Discovered & Resolved

| Issue | Root Cause | Fix Applied |
|---|---|---|
| Unused TypeScript import | `CompareFoods.tsx` imported unused `NutritionData` | Removed unused import; `npm run build` completed with zero warnings. |
| Pytest Module Import Failure | `app` package not on `sys.path` during pytest collection | Created `pytest.ini` with `pythonpath = .` and configured `asyncio_mode = auto`. |
| Sentence-Transformers lazy loading | Module not present in initial minimal environment | Added lazy initialization pattern in `rag_service.py` to prevent backend startup crashes if vector search models are downloading. |

---

## 5. Remaining Tasks & Next Steps

1. Configure production `GEMINI_API_KEY` and `USDA_API_KEY` for live deployment.
2. Package frontend static build into backend static file serving or deploy frontend to Vercel and backend to Render/Google Cloud Run.
3. Finalize presentation slides based on `docs/PRESENTATION_OUTLINE.md`.
