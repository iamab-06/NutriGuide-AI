# NutriGuide AI — Problem Statement & Objectives

**Institution:** Department of Computer Science and Engineering, Siddaganga Institute of Technology  
**Project:** NutriGuide AI  
**Academic Year:** 2026  

---

## 1. Problem Statement

Modern dietary habits are increasingly linked to the rise of non-communicable lifestyle diseases, including type-2 diabetes, hypertension, cardiovascular disorders, and obesity. Simultaneously, food allergies and sensitivities affect an estimated 10% of adults and 8% of children globally. Despite widespread access to smartphones and digital health tools, individuals struggle to maintain consistent dietary awareness due to four systemic bottlenecks:

1. **High Friction in Food Logging:** Traditional dietary management apps (e.g., MyFitnessPal, Cronometer) mandate manual text entry, recipe searching, or guesswork regarding portion sizes. This manual burden leads to a reported user abandonment rate exceeding 70% within the first month.
2. **Visual Food Recognition Fragility:** Emerging computer vision food recognizers frequently fail under real-world visual variance (e.g., mixed ingredients, varying lighting, regional preparation styles). More critically, existing systems output forced, uncalibrated predictions—arbitrarily displaying wrong dishes with false high confidence—and retrieve incorrect nutrition facts without notifying the user of classification uncertainty.
3. **Unverified & Hallucinatory Nutritional Data:** Consumer nutritional databases often rely on crowdsourced, uncurated user uploads rife with missing fields, inaccurate caloric values, and conflicting serving sizes. Conversely, when users ask general-purpose Large Language Models (LLMs) like ChatGPT or standard Gemini about nutritional values, the models frequently hallucinate numerical quantities, fabricate daily value percentages, or dispense ungrounded medical advice.
4. **Opaque Packaged Food Ingredients & Hidden Allergens:** Consumers purchasing packaged goods face dense, multilingual ingredient lists printed in microscopic typography on product packaging. Community databases like Open Food Facts provide valuable crowd-sourced information, but failing to distinguish between confirmed absence of allergens and unrecorded database fields introduces severe health hazards for allergic consumers.

---

## 2. Project Objectives

### 2.1 Primary Objectives
1. **Accurate & Efficient Food Image Classification:** Train and deploy a lightweight convolutional neural network capable of recognizing 20 common food categories with $\ge 85\%$ Top-1 accuracy and sub-50 ms inference latency on standard consumer hardware.
2. **Transparent Uncertainty Gating & Multimodal Fallback:** Formulate a calibrated confidence threshold ($70\%$) that prevents unverified food acceptance. For ambiguous predictions ($< 70\%$), seamlessly invoke a multimodal vision fallback (Google Gemini Vision) while strictly withholding definitive nutrition information until the user explicitly confirms the food identity.
3. **Standardized Nutrition Intelligence:** Interface with the authoritative **USDA FoodData Central API** (Foundation and SR Legacy datasets) to extract standardized macronutrient and micronutrient metrics normalized to a uniform **per 100g basis**.
4. **Ingredient & Allergen Transparency:** Integrate the **Open Food Facts API** to enable real-time packaged food search and barcode lookup, extracting declared allergens and explicitly warning users when database records are incomplete.
5. **Evidence-Grounded RAG Assistant:** Develop a Retrieval-Augmented Generation pipeline using **Sentence Transformers (`all-MiniLM-L6-v2`)** and a **FAISS L2 Flat Vector Index** over a curated 20-topic nutrition knowledge base. Construct structured prompts for **Google Gemini 1.5/2.x** to provide factual, verifiable conversational answers devoid of numerical hallucination.
6. **Unified, Responsive Web Interface:** Design and deliver a production-ready, accessible web application in **React 19, TypeScript, and Vite 8**, styled with an approved forest-green and white aesthetic (`#0d2818`, `#2d6a4f`, `#52b788`).

---

## 3. Scope of the Project

### 3.1 In-Scope Components
- Fine-tuning and inference of **MobileNetV3-Large** across 20 representative Food-101 categories:
  - *Apple Pie, Caesar Salad, Chicken Curry, Chocolate Cake, Donuts, French Fries, Fried Rice, Hamburger, Hot Dog, Ice Cream, Omelette, Pancakes, Pizza, Ramen, Samosa, Spaghetti Bolognese, Spring Rolls, Steak, Sushi, Waffles.*
- Asynchronous FastAPI backend server providing 6 modular REST routes (`/analyze`, `/nutrition`, `/products`, `/chat`, `/compare`, `/health`).
- Multimodal fallback using Google Gemini Vision Studio APIs for low-confidence food inputs.
- USDA FoodData Central integration for 9 core nutrient attributes: Energy (kcal), Protein (g), Carbohydrates (g), Total Fat (g), Sugars (g), Dietary Fiber (g), Sodium (mg), Cholesterol (mg), and Saturated Fat (g).
- Offline fallback to local USDA Standard Reference dataset during network disruption or upstream API quota exhaustion.
- Open Food Facts search and EAN-13 barcode parsing with multi-host failover.
- Side-by-side per-100g comparative nutritional analysis of arbitrary foods with automated AI comparison narratives.
- Multi-turn conversational nutrition assistant grounded by FAISS vector retrieval and automated food entity detection.
- Comprehensive automated test suite (37 unit/integration tests) and empirical latency benchmarks.

### 3.2 Out-of-Scope (Future Enhancements)
- Continuous video stream segmentation and 3D volume/weight estimation.
- Medical diagnostics, chronic disease prescription, or clinical dietary plans.
- User account authentication, personalized biometric tracking, and cloud database persistence (designed as a stateless privacy-first privacy tool).
- Native iOS/Android mobile compilations (application is fully responsive for mobile web browsers).

---

## 4. Design Constraints & Guiding Principles

1. **Security & Privacy First:** No user credentials or API keys (`GEMINI_API_KEY`, `USDA_API_KEY`) are exposed in source code, client responses, or version control. Keys are loaded exclusively through server-side `.env` files with string masking in logs.
2. **Defensive Nutrition Withholding:** The system prioritizes nutritional safety over forced speed. If food identification is uncertain ($< 70\%$), nutritional facts are withheld until user confirmation to prevent false dietary beliefs.
3. **Stateless Scalability:** Core APIs remain stateless, facilitating horizontal scaling and zero-retention privacy for uploaded personal meal imagery.
4. **Computational Efficiency:** The local vision model runs in $\approx 25\text{ ms}$ on standard CPUs, eliminating the need for expensive dedicated GPU cloud servers for primary classification.
