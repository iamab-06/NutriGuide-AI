# NutriGuide AI — Engineering & Development Challenges

**Project:** NutriGuide AI  
**Institution:** Department of Computer Science and Engineering, Siddaganga Institute of Technology  
**Academic Year:** 2026  

---

## 1. Executive Summary of Engineering Challenges

During the design, implementation, and empirical verification of NutriGuide AI, several technical bottlenecks emerged across machine learning, asynchronous distributed systems, API integration, and user experience. This document records the 16 major engineering challenges encountered, their observable symptoms, root causes, technical resolutions, and remaining limitations.

---

## 2. Granular Challenge Analysis

### Challenge 1: Food Classification Inaccuracy & Untrained Linear Head
- **Problem:** When uploaded food images were classified, MobileNetV3 produced incorrect predictions with near-random confidence (e.g., Samosa predicted as Waffles at 6.8%, Chocolate Cake as Waffles at 6.9%).
- **Root Cause:** While the convolutional feature extractor was pretrained on ImageNet-1k, the custom linear classification head (`nn.Linear(960, 20)`) had been randomly initialized without fine-tuning weights saved to disk. Baseline Top-1 accuracy was only **2.60%**.
- **Resolution:** Implemented `train_food20.py` to fine-tune the head and top convolutional stages on 15,000 Food-101 images over 10 epochs. Saved verified checkpoint `backend/models/nutriguide_classifier.pth` (17.1 MB), boosting Top-1 accuracy to **90.64%** and Top-3 accuracy to **97.82%**.
- **Verification:** Verified via `evaluate_classifier.py` across 5,000 unseen test images.

---

### Challenge 2: False Certainty on Ambiguous Dishes & Low Threshold Gating
- **Problem:** An image of a samosa was classified as Apple Pie with 43.9% confidence. The system accepted Apple Pie as definitive truth and fetched Apple Pie nutritional facts.
- **Root Cause:** The classification threshold was originally set at `0.40 (40%)`. Because $43.9\% \ge 40\%$, the backend marked `is_confident = True` and bypassed the multimodal fallback.
- **Resolution:** Re-calibrated `CONFIDENCE_THRESHOLD = 0.70 (70%)`. Any prediction under 70% is marked `is_confident = False` and triggers the Gemini Vision multimodal fallback.
- **Verification:** Tested via `test_food_identification_fallback.py`, confirming ambiguous samosa images trigger Gemini Vision.

---

### Challenge 3: Inappropriate Nutrition Delivery on Unconfirmed Foods
- **Problem:** When Gemini Vision identified an alternative dish, the backend was automatically fetching nutrition for Gemini's recommendation without giving the user an opportunity to review or correct it.
- **Root Cause:** The system conflated recommendation with user confirmation, risking false dietary advice if Gemini also misidentified the dish.
- **Resolution:** Enforced a **Strict Nutrition Withholding Policy**: whenever prediction is uncertain, `nutrition = None`. The frontend displays candidate chips, a manual dropdown, and a prominent one-click button: `"Confirm [Food] & View Nutrition"`. Definitive nutrition is only fetched upon user action.
- **Verification:** Verified in `test_food_identification_fallback.py` and automated user journey 5.

---

### Challenge 4: Gemini SDK Thread Blocking in FastAPI Event Loop
- **Problem:** High concurrency requests to `/api/chat` caused the FastAPI server to freeze and become unresponsive to other HTTP requests.
- **Root Cause:** The official `google-generativeai` SDK uses synchronous, blocking gRPC calls under the hood. Calling `chat.send_message()` directly inside an `async def` route blocked the single-threaded asyncio event loop.
- **Resolution:** Offloaded the synchronous Gemini SDK call to a worker thread using `asyncio.to_thread(chat.send_message, ...)` combined with a 10.0-second timeout.
- **Verification:** Verified high-load concurrent requests in `test_gemini.py` without server stalls.

---

### Challenge 5: Gemini API Quota Exhaustion & Cloud Failover
- **Problem:** Free-tier Gemini endpoints occasionally returned HTTP 429 (Resource Exhausted) during burst testing.
- **Root Cause:** Upstream rate limits on `gemini-1.5-flash` during peak academic development hours.
- **Resolution:** Implemented an automated candidate failover hierarchy:
  `gemini-3.5-flash` $\to$ `gemini-3.5-flash-lite` $\to$ `gemini-3.1-flash-lite` $\to$ `gemini-flash-latest` $\to$ `gemini-3.8-flash`.
- **Verification:** Verified fallback logic in `test_gemini.py` using simulated rate-limit exceptions.

---

### Challenge 6: USDA API Rate Limits & Local Reference Fallback
- **Problem:** Default USDA FoodData Central requests using `DEMO_KEY` hit the strict 30 requests/hour limit, causing nutrition lookups to fail.
- **Root Cause:** Upstream IP-based rate limiting on unauthenticated demo keys.
- **Resolution:** Enabled personal API key loading via `USDA_API_KEY` in `backend/.env`. Additionally, embedded a verified local dictionary (`USDA_REFERENCE_DATA`) in `backend/app/core/categories.py` as an automatic fallback when upstream is unreachable or rate-limited.
- **Verification:** Verified real USDA request returning 10 pizza items with HTTP 200, and verified offline fallback when network is mocked.

---

### Challenge 7: Secret Key Exposure Vulnerabilities
- **Problem:** Standard object inspection or debugging statements like `print(settings)` exposed raw API keys in application logs.
- **Root Cause:** Pydantic's default `BaseSettings.__repr__` prints all field values in plain text.
- **Resolution:** Overrode `__repr__` in `backend/app/core/config.py` to mask `gemini_api_key` and `usda_api_key` as `"***"`. Added `.gitignore` validation to guarantee `.env` is never committed.
- **Verification:** Verified via `test_gemini_key_never_exposed_in_config` in `test_gemini.py`.

---

### Challenge 8: Open Food Facts Upstream Timeouts & Multi-Host Failover
- **Problem:** Occasional latency spikes or connection timeouts from `world.openfoodfacts.org`.
- **Root Cause:** Open Food Facts is a community-funded public infrastructure subject to periodic regional traffic surges.
- **Resolution:** Implemented automatic multi-host failover between `world.openfoodfacts.org` and `world.openfoodfacts.net`, backed by custom `User-Agent` headers and a 15-second timeout.
- **Verification:** Tested in `test_products.py` across name search and barcode lookup.

---

### Challenge 9: LLM Numerical Hallucination in Dietary Advice
- **Problem:** Standard Gemini prompts generated plausible-sounding but completely fabricated calorie and macronutrient numbers for food queries.
- **Root Cause:** Generative LLMs generate tokens probabilistically rather than retrieving deterministic arithmetic values from memory.
- **Resolution:** Built a strict **Evidence-Grounding Pipeline**:
  1. Auto-detected food entities in queries.
  2. Injected verified USDA nutrition data into the prompt context.
  3. Bound system instructions forbidding the invention of numbers and demanding citation of sources.
- **Verification:** Tested in `test_build_nutrition_context_complete` in `test_gemini.py`.

---

### Challenge 10: RAG Vector Search Recall & Semantic Drift
- **Problem:** Naive keyword searches failed to retrieve appropriate nutrition documents when users used colloquial phrasing (e.g., *"carbs in sweet things"* vs *"glycemic index"*).
- **Root Cause:** Keyword matching lacks semantic understanding.
- **Resolution:** Deployed dense vector search using `sentence-transformers/all-MiniLM-L6-v2` and `FAISS IndexFlatL2`. Vectors capture conceptual similarity regardless of exact lexical overlap.
- **Verification:** Verified in `test_rag_service_fallback_or_retrieve` in `test_rag.py`.

---

### Challenge 11: Cross-Origin Resource Sharing (CORS) & Reverse Proxy Configuration
- **Problem:** Frontend fetch requests from `http://localhost:5173` to `http://localhost:8000` were blocked by browser CORS security policies during initial development.
- **Root Cause:** Differing port origins between Vite development server (5173) and FastAPI ASGI server (8000).
- **Resolution:** Configured `CORSMiddleware` in FastAPI with explicit allowed origins (`http://localhost:5173`, `http://127.0.0.1:5173`). In addition, configured Vite's reverse proxy in `frontend/vite.config.ts` to map `/api` requests directly to backend port 8000.
- **Verification:** Verified seamless end-to-end user journeys through the Vite proxy in `verify_journeys.py`.

---

### Challenge 12: React 19 & Tailwind CSS v4 Build Compatibility
- **Problem:** Migrating to Tailwind CSS v4 introduced build errors due to deprecated `tailwind.config.js` directives and PostCSS plugin changes.
- **Root Cause:** Tailwind v4 switched to a native CSS-first engine utilizing `@theme` directives instead of JavaScript configuration files.
- **Resolution:** Refactored `frontend/src/index.css` to use native `@import "tailwindcss";` directives and configured Vite's `@tailwindcss/vite` plugin.
- **Verification:** Frontend production build (`npm run build`) compiles cleanly in 1.20s with 0 errors.

---

### Challenge 13: In-Memory Server Environment Desynchronization
- **Problem:** Adding a new API key to `backend/.env` while Uvicorn was actively running did not take effect, causing requests to continue using cached credentials.
- **Root Cause:** Operating system processes load environment variables into memory at startup; file edits on disk do not alter existing process memory without a restart.
- **Resolution:** Implemented process lifecycle management: terminated the stale Uvicorn worker and restarted a clean process to load the newly written `.env` file.
- **Verification:** Verified live USDA API returned 200 OK with the newly configured user key.

---

### Challenge 14: Allergen Absence Safety Ambiguity
- **Problem:** Users viewing packaged foods assumed that products with empty allergen tags were guaranteed to be allergen-free.
- **Root Cause:** Open Food Facts is crowd-sourced; missing allergen data simply reflects unrecorded fields, not verified chemical absence.
- **Resolution:** Added prominent contextual warning badges on all packaged product views: *"No allergens declared in database. This does NOT confirm the product is allergen-free. Always check physical packaging."*
- **Verification:** Verified in `IngredientsAllergens.tsx` and integration tests.

---

### Challenge 15: Visual UI Clutter & Academic Branding Overload
- **Problem:** The dashboard interface was cluttered with generic rainbow gradient icons, trailing footer watermarks, and artificial status indicators that detracted from usability.
- **Root Cause:** Early template scaffolding accumulated visual elements that conflicted with the clean forest-green brand guidelines.
- **Resolution:** Refined layout and dashboard components:
  1. Removed `NutriGuide AI • SIT CSE 2026` footer clutter.
  2. Removed pulsating `System Active` status indicator.
  3. Removed yellow disclaimer banner from dashboard and top of allergens page.
  4. Streamlined AI Assistant header to remove robot logo and redundant labels.
  5. Standardized feature cards on unified emerald icon boxes (`#e8f4ed` background with `#2d6a4f` icons).
- **Verification:** Verified clean visual hierarchy and 100% responsive alignment across all views.

---

### Challenge 16: Cloud LLM Deprecation & Migration to Local Google Gemma 3 4B IT (via Ollama)
- **Problem:** Cloud-hosted Gemini APIs introduced operational vulnerability: external API quotas (`ResourceExhausted` 429), recurring cloud latency, data transmission privacy concerns for user meal photos, and dependency on external API credentials.
- **Root Cause:** Direct architectural reliance on remote proprietary cloud endpoints (`google.generativeai`) for core multimodal reasoning and conversational intelligence.
- **Resolution:** Fully migrated all generative AI workloads to a local **Google Gemma 3 4B IT** model deployed via **Ollama** (`http://localhost:11434`):
  1. Built `backend/app/services/ollama_service.py` to support multimodal vision fallback (`classify_food_with_vision`), grounded chat (`chat_with_context`), and side-by-side food comparison (`explain_nutrition`).
  2. Implemented non-blocking asynchronous HTTP execution via `httpx.AsyncClient` with split connection timeouts (`connect=5.0s`, `total=120s`) to ensure the FastAPI event loop never hangs if Ollama is offline.
  3. Maintained 100% API schema backwards compatibility across `/api/analyze`, `/api/chat`, and `/api/compare` so frontend contracts remained perfectly stable.
  4. Updated UI text badges across Dashboard, AI Assistant, Food Comparison, and Image Analysis to showcase the local Gemma 3 4B model.
- **Verification:** All 51 backend tests passed (100% pass rate in 61s); frontend built cleanly in 2.19s with zero errors.

---

### Challenge 17: LLM Evasive Refusal & Hardcoded Knowledge Dependency on General Nutrition Queries
- **Problem:** When users asked practical dietary queries such as *"Which is high in protein 250gms chicken breast or 10 whole eggs?"*, the AI Nutrition Assistant gave evasive responses refusing to provide a straight answer (e.g., stating *"data is not provided in your knowledge base"*).
- **Root Cause:** Two compounding design flaws:
  1. *Rigid Negative Prompting Constraint:* The original system prompt strictly commanded: *"If specific nutrition, ingredient, or allergen data is absent or unavailable, explicitly inform the user rather than inventing numbers."* Small instruction-tuned models like Gemma 3 followed this literally to a fault, rejecting any query whose specific food wasn't explicitly injected in the prompt context.
  2. *Narrow 20-Category Entity Matching:* The entity detector was hardcoded to only search for the 20 Food-101 categories. When users asked about everyday staples (chicken breast, eggs, salmon, tofu, oats, banana), the backend failed to recognize them and injected zero nutritional context.
- **Resolution:**
  1. Built multi-entity food detection in `backend/app/api/chat.py` (`_extract_candidate_food_terms` and `_match_reference_food`) supporting plurals, compound phrases, and foundational staples.
  2. Expanded in-memory verified USDA reference data (`USDA_REFERENCE_DATA`) to include foundational staple foods with exact per-100g USDA values.
  3. Added real-time asynchronous fallback querying directly to live USDA FoodData Central with a 3.0s timeout for unindexed foods.
  4. Engineered an updated prompt architecture in `ollama_service.py`:
     - Mandatory direct conclusion in sentence one.
     - Explicit step-by-step arithmetic for user-specified portions (e.g. 250g chicken breast = 77.5g protein vs 10 whole eggs = 63g protein).
     - Instruction to use attached context when available and seamlessly leverage standard USDA FoodData Central baselines when records are absent, eliminating evasive refusal.
     - Strict 150-word brevity budget, cutting generation time from ~55s to 10–18s on RTX 3050 Laptop GPU.
- **Verification:** Tested live on user query; assistant immediately returned straightforward, mathematically precise answer: *"250 grams of cooked chicken breast is higher in protein than 10 whole eggs..."* with exact calculations. All 51 backend tests pass.
