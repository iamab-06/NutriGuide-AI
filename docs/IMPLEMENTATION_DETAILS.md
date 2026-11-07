# NutriGuide AI — Comprehensive Implementation Details

**Project:** NutriGuide AI  
**Institution:** Department of Computer Science and Engineering, Siddaganga Institute of Technology  
**Academic Year:** 2026  

---

## 1. Directory Structure & Source Code Organization

```text
NutriGuide-AI/
|-- backend/
|   |-- app/
|   |   |-- api/
|   |   |   |-- __init__.py
|   |   |   |-- analyze.py              # Vision & image classification route
|   |   |   |-- chat.py                 # Multi-turn RAG assistant route
|   |   |   |-- compare.py              # Food comparison route
|   |   |   |-- health.py               # Healthcheck & category catalog route
|   |   |   |-- nutrition.py            # USDA nutrition search & lookup route
|   |   |   |-- products.py             # Open Food Facts packaged goods route
|   |   |-- core/
|   |   |   |-- __init__.py
|   |   |   |-- categories.py           # 20 Food categories, display names, USDA mappings
|   |   |   |-- config.py               # Pydantic Settings & environment variable loader
|   |   |-- models/                     # Package init
|   |   |-- rag/
|   |   |   |-- __init__.py
|   |   |   |-- rag_service.py          # SentenceTransformer + FAISS semantic retrieval
|   |   |-- schemas/
|   |   |   |-- __init__.py
|   |   |   |-- food.py                 # Pydantic models (Analyze, Nutrition, Chat, etc.)
|   |   |-- services/
|   |   |   |-- __init__.py
|   |   |   |-- classifier.py           # PyTorch MobileNetV3-Large vision engine
|   |   |   |-- gemini_service.py       # Google Gemini 1.5/2.x API & vision fallback
|   |   |   |-- nutrition.py            # USDA FoodData Central HTTPX client
|   |   |   |-- openfoodfacts.py        # Open Food Facts HTTPX client
|   |   |-- utils/                      # Helper utilities
|   |   |-- main.py                     # FastAPI app factory, CORS, lifespan handlers
|   |-- datasets/
|   |   |-- food20/                     # Food-101 20-class dataset (15k train, 5k val)
|   |-- models/
|   |   |-- nutriguide_classifier.pth   # Fine-tuned PyTorch weights (17.1 MB)
|   |   |-- training_log.json           # 10-Epoch training convergence log
|   |-- tests/                          # 9 Automated test suites (37 test cases)
|   |   |-- test_classifier.py
|   |   |-- test_compare.py
|   |   |-- test_food_identification_fallback.py
|   |   |-- test_gemini.py
|   |   |-- test_health.py
|   |   |-- test_nutrition.py
|   |   |-- test_products.py
|   |   |-- test_rag.py
|   |   |-- test_vision_improvements.py
|   |   |-- benchmark.py                # Latency & coverage benchmark runner
|   |   |-- verify_journeys.py          # End-to-end user journey verification
|   |-- .env                            # Local environment variables (Git ignored)
|   |-- .env.example                    # Template with dummy placeholders
|   |-- pytest.ini                      # Test runner configuration
|   |-- requirements.txt                # Backend dependencies
|
|-- frontend/
|   |-- src/
|   |   |-- components/
|   |   |   |-- ConfidenceBadge.tsx     # Visual confidence indicator
|   |   |   |-- ErrorMessage.tsx        # Standardized error component
|   |   |   |-- Layout.tsx              # Sidebar, topbar, responsive shell
|   |   |   |-- LoadingSpinner.tsx      # Branded animated status indicator
|   |   |   |-- NutritionCard.tsx       # Standardized per-100g nutrient breakdown
|   |   |-- pages/
|   |   |   |-- AIAssistant.tsx         # Multi-turn RAG nutrition chat
|   |   |   |-- AnalyzeFood.tsx         # Food image upload & verification
|   |   |   |-- CompareFoods.tsx        # Side-by-side food comparison
|   |   |   |-- Dashboard.tsx           # Home dashboard with feature cards & stats
|   |   |   |-- IngredientsAllergens.tsx# Open Food Facts product/barcode explorer
|   |   |   |-- NutritionInfo.tsx       # USDA FoodData Central search engine
|   |   |-- services/
|   |   |   |-- api.ts                  # Axios HTTP client with typed endpoints
|   |   |-- types/
|   |   |   |-- index.ts                # TypeScript interface definitions
|   |   |-- App.tsx                     # Route declarations
|   |   |-- main.tsx                    # React DOM root mounting
|   |   |-- index.css                   # Tailwind CSS v4 directives
|   |-- package.json                    # Frontend dependencies & scripts
|   |-- vite.config.ts                  # Vite 8 config with reverse proxy
|
|-- docs/                               # Complete project documentation package
|-- README.md                           # Master project README
```

---

## 2. Backend Implementation Details

### 2.1 Food Classification Service (`backend/app/services/classifier.py`)
- **Singleton Lifecycle:** Initialized via `get_classifier()` on first access.
- **Model Instantiation:** Builds `torchvision.models.mobilenet_v3_large(weights=None)` and replaces `model.classifier[3]` with `nn.Linear(960, 20)`.
- **Checkpoint Loading:** Loads `backend/models/nutriguide_classifier.pth` onto `cuda` or `cpu` using `torch.load(..., weights_only=True)`.
- **Preprocess Pipeline:**
  ```python
  PREPROCESS = transforms.Compose([
      transforms.Resize(256),
      transforms.CenterCrop(224),
      transforms.ToTensor(),
      transforms.Normalize(
          mean=[0.485, 0.456, 0.406],
          std=[0.229, 0.224, 0.225]
      ),
  ])
  ```
- **Prediction Logic:** Executes `torch.softmax(logits, dim=1)` and returns top-5 candidate classes with formatted percentage strings.
- **Confidence Gate:** Evaluates whether top prediction confidence satisfies `CONFIDENCE_THRESHOLD = 0.70`.

### 2.2 Multimodal Fallback Service (`backend/app/services/gemini_service.py`)
- **Visual Fallback Trigger:** `classify_food_with_gemini(image_bytes)` converts raw bytes into a `PIL.Image` and packages it into a multimodal part for Gemini Flash.
- **Structured JSON Instruction:** Enforces structured output format:
  ```json
  {
    "suggested_food": "Samosa",
    "confidence": "High",
    "explanation": "Triangular pastry with crisp fried crust and savory vegetable filling.",
    "category_match": "samosa"
  }
  ```
- **Candidate Hierarchy & Failover:** Sequentially attempts execution across:
  `gemini-3.5-flash` $\to$ `gemini-3.5-flash-lite` $\to$ `gemini-3.1-flash-lite` $\to$ `gemini-flash-latest` $\to$ `gemini-3.8-flash`.
- **Thread Isolation:** Runs synchronous SDK network calls inside `asyncio.to_thread` with a strict 10.0-second timeout, avoiding event-loop deadlock.

### 2.3 Nutrition Service (`backend/app/services/nutrition.py`)
- **USDA FoodData Central Ingestion:** Queries `https://api.nal.usda.gov/fdc/v1/foods/search` with `dataType: ["Foundation", "SR Legacy"]`.
- **Standardized Nutrient IDs:**
  - `calories`: 1008 (kcal)
  - `protein`: 1003 (g)
  - `carbohydrates`: 1005 (g)
  - `fat`: 1004 (g)
  - `sugar`: 2000 (g)
  - `fiber`: 1079 (g)
  - `sodium`: 1093 (mg)
  - `cholesterol`: 1253 (mg)
  - `saturated_fat`: 1258 (g)
- **Local Fallback:** If upstream USDA times out or rate limits, matches food against `USDA_REFERENCE_DATA` and marks `source: "USDA FoodData Central (Standard Reference)"`.

### 2.4 Open Food Facts Service (`backend/app/services/openfoodfacts.py`)
- **Endpoints:** Search API (`/cgi/search.pl`) and Barcode API (`/api/v2/product/{barcode}.json`).
- **Resilience:** Implements automatic host failover between `world.openfoodfacts.net` and `world.openfoodfacts.org` with configured `User-Agent`.
- **Allergen Extraction:** Parses `allergens_tags` (e.g., `en:milk`, `en:soybeans`) and formats readable labels.

### 2.5 RAG Knowledge Retrieval (`backend/app/rag/rag_service.py`)
- **Index Lifecycle:** Loads 20 curated nutrition documents upon startup, computes 384-dimensional embeddings with `all-MiniLM-L6-v2`, and populates `faiss.IndexFlatL2`.
- **Query Search:** Encodes conversational query text into a vector, queries the index for nearest neighbors ($k=2$), and returns formatted domain knowledge chunks.

---

## 3. Frontend Implementation Details

### 3.1 State Management & API Client (`frontend/src/services/api.ts`)
- **Axios Instance:** Base URL defaults to `/api` (proxied by Vite to `http://127.0.0.1:8000`).
- **Global Error Interceptor:** Normalizes FastAPI error formats (`detail`, `message`) into human-readable Error instances.
- **Type Safety:** Typed responses ensure components consume verified structures without manual casting.

### 3.2 Food Analysis Workflow (`frontend/src/pages/AnalyzeFood.tsx`)
- **File Validation:** Rejects files $>10\text{ MB}$ or non-image types (`image/jpeg`, `image/png`, `image/webp`).
- **Dual Display Flow:**
  - If `is_confident === true`: Renders top food prediction and `NutritionCard` immediately.
  - If `is_confident === false`: Withholds `NutritionCard`, displays Gemini Vision recommendation card with one-click **"Confirm & View Nutrition"** button, alternative prediction chips, and manual dropdown.
- **Manual Confirmation Callback:** `handleSelectAlternative(candidate)` fetches verified USDA nutrition for the confirmed dish, transforming state to confirmed.

### 3.3 Visual Identity & Layout Shell (`frontend/src/components/Layout.tsx`)
- **Approved Theme:** Forest green sidebar (`#0d2818`), emerald accents (`#52b788`), white card surfaces, subtle borders (`border-gray-100`).
- **Minimalist Cleanliness:** Topbar displays only the mobile hamburger button and active route title. Trailing footer branding and simulated status indicators have been cleanly removed for an uncluttered user experience.
