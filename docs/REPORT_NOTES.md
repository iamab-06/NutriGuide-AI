# NutriGuide AI — Academic Report Preparation Notes

**Course / Degree:** Bachelor of Engineering in Computer Science & Engineering  
**Institution:** Siddaganga Institute of Technology, Tumakuru  
**Academic Target Date:** 30 October 2026  
**Document Purpose:** Source notes and section drafts for the academic final project report.

---

## 1. Abstract

Nutritional transparency is a critical determinant of public health, yet existing dietary assessment tools rely heavily on manual text logging, coarse portion estimations, or black-box generative AI chatbots prone to nutritional hallucination. This project presents **NutriGuide AI**, an end-to-end multimodal Generative AI web platform that unifies Computer Vision, authoritative nutrition databases, community packaged-food repositories, and Retrieval-Augmented Generation (RAG). 

Using a lightweight **MobileNetV3-Large** deep convolutional neural network, the system classifies food images across 20 canonical categories with an empirical inference latency of **~25 ms** on commodity hardware, gated by an explicit 40% confidence threshold to prevent false confirmations. Upon identification, verified nutrient metrics (energy, protein, carbohydrates, lipids, fiber, sugar, sodium) are retrieved on a standardized **per-100g basis** from the **USDA FoodData Central** database. Packaged products are cross-referenced with the **Open Food Facts** API to surface verified ingredient lists and allergen tags with proactive safety disclaimers. 

For qualitative queries, a hybrid RAG pipeline leverages dense vector embeddings via **Sentence Transformers** (`all-MiniLM-L6-v2`) and **FAISS** indexing over a curated domain knowledge base to constrain **Google Gemini 1.5 Flash**, enforcing evidence-grounded generation and eliminating fabricated nutritional claims. Evaluation across ten faculty criteria confirms 100% entity mapping coverage, robust uncertainty handling, and a clean, responsive user experience.

---

## 2. Problem Statement

Modern consumers face significant obstacles in understanding the nutritional composition and safety of the food they consume:
1. **Manual Logging Friction:** Traditional diet-tracking apps require tedious manual text entry and portion guessing, leading to low user compliance.
2. **Nutritional Hallucination in GenAI:** General-purpose Large Language Models (LLMs) frequently hallucinate numerical macro/micronutrient amounts when asked for nutritional advice, creating genuine health and safety hazards.
3. **Inconsistent Portion Reporting:** Nutrition labels alternate arbitrarily between per-serving, per-container, and per-package measurements, confounding direct nutritional comparisons.
4. **Allergen Ambiguity:** Undeclared allergens and missing product data often go uncommunicated, creating false impressions of product safety for sensitive individuals.

---

## 3. Objectives

The primary objectives of the NutriGuide AI project are:
1. **Automated Visual Recognition:** Develop an efficient deep learning model based on MobileNetV3 capable of identifying food items rapidly on CPU/edge devices.
2. **Grounded Empirical Retrieval:** Build an API pipeline that interfaces with USDA FoodData Central to extract standardized, unadulterated nutrient profiles on a per-100g basis.
3. **Packaged Product Intelligence:** Integrate Open Food Facts to deliver ingredient and allergen transparency with explicit missing-field notices.
4. **Hallucination-Proof AI Assistant:** Construct a RAG pipeline utilizing FAISS vector retrieval coupled with strict prompt boundaries to guide Gemini 1.5 Flash in explaining nutrition facts without inventing numbers.
5. **Standardized Food Comparison:** Enable side-by-side per-100g comparison of foods with algorithmic superiority detection.
6. **Responsible Uncertainty Communication:** Implement strict threshold gating to prevent unconfident or ambiguous inputs from being presented as confirmed facts.

---

## 4. Proposed Methodology

```
[Food Image Input] ──> [MobileNetV3 Inference] ──> [Confidence Check (>= 40%)]
                                                           │
                                        ┌──────────────────┴──────────────────┐
                                        ▼                                     ▼
                                  [Pass: Confident]                 [Fail: Ambiguous]
                                        │                                     │
                             [USDA Entity Normalization]             [Prompt User Confirmation]
                                        │
                             [Per-100g Nutrient Fetch]
                                        │
        ┌───────────────────────────────┴───────────────────────────────┐
        ▼                                                               ▼
 [Direct UI Rendering]                                       [RAG Knowledge Pipeline]
 [NutritionCard Component]                                    [Sentence Transformers]
                                                                        │
                                                                 [FAISS Search]
                                                                        │
                                                            [Evidence-Bound Gemini]
                                                                        │
                                                            [Verified AI Explanation]
```

---

## 5. Technology Selection & Rationale

| Layer | Chosen Technology | Alternatives Evaluated | Rationale |
|---|---|---|---|
| **Frontend Framework** | React 19 + TypeScript | Vue, Angular | Robust typing, component reusability, widespread enterprise support. |
| **Build & Styling** | Vite 8 + Tailwind CSS v4 | Webpack, plain CSS | Instant HMR, minimal bundle footprint, standardized utility design system. |
| **Backend Framework** | FastAPI + Python 3.12 | Flask, Django, Node.js | Native asynchronous I/O, automatic OpenAPI schema generation, Pydantic type safety. |
| **Vision Backbone** | MobileNetV3-Large | ResNet-50, Vision Transformer | High parameter efficiency (~5.4M params), sub-30ms CPU inference, low memory overhead. |
| **Primary Data Source** | USDA FoodData Central | Nutritionix, Edamam | Authoritative public scientific reference data, transparent nutrient IDs, no proprietary lock-in. |
| **Product Data Source** | Open Food Facts | Spoonacular | Open collaborative global dataset, open barcode resolution, detailed allergen tags. |
| **Vector Indexing** | FAISS + Sentence Transformers | ChromaDB, Pinecone | In-process, zero cloud infrastructure cost, fast dense vector search on CPU. |
| **Generative LLM** | Google Gemini 1.5 Flash | Local Llama 3, OpenAI GPT-4 | Native multimodal support, low latency, extensive free tier through Google AI Studio. |

---

## 6. Dataset Descriptions & Data Provenance

1. **Food-101 Subset (Vision):**
   - Source: Computer Vision Laboratory, ETH Zurich.
   - Selected Subset: 20 culturally diverse and nutritionally distinct categories (Apple Pie, Caesar Salad, Chicken Curry, Chocolate Cake, Donuts, French Fries, Fried Rice, Hamburger, Hot Dog, Ice Cream, Omelette, Pancakes, Pizza, Ramen, Samosa, Spaghetti Bolognese, Spring Rolls, Steak, Sushi, Waffles).
2. **USDA FoodData Central:**
   - Source: U.S. Department of Agriculture, Agricultural Research Service.
   - Datasets queried: Foundation Foods, National Nutrient Database for Standard Reference (SR Legacy), Food and Nutrient Database for Dietary Studies (FNDDS).
3. **Open Food Facts Database:**
   - Source: Open Food Facts non-profit open database (ODbL).
   - Fields extracted: Ingredients list, allergen categories, brand owner, barcode.
4. **NutriGuide Curated Nutrition Knowledge Base:**
   - 20 verified reference texts covering macronutrient metabolism, dietary fiber, glycemic index, major food allergens (US/EU definitions), and food-specific nutritional profiles.

---

## 7. Implementation Status vs Planned Enhancements

### Completed & Verified:
- [x] Full-stack architecture (FastAPI backend + React frontend).
- [x] MobileNetV3 image classification inference with confidence score gating.
- [x] USDA FoodData Central nutrient extraction across 9 core nutrient parameters.
- [x] Open Food Facts name and barcode lookup with allergen identification.
- [x] Google Gemini 1.5 Flash evidence-grounded chat integration.
- [x] FAISS semantic retrieval over curated knowledge base.
- [x] Side-by-side per-100g comparative analysis with AI summarization.
- [x] Automated test suite (15 unit/integration tests with 100% pass rate).
- [x] Real measured benchmark suite (classification latency: 25.38 ms avg).

### Planned Future Work:
- [ ] On-device OCR for physical ingredient label scanning using Tesseract / PaddleOCR.
- [ ] Multi-label semantic segmentation for mixed-dish meal plate estimation.
- [ ] User profile personalization for specific allergen exclusion alerts.

---

## 8. Results & Discussion

- **Vision Performance:** MobileNetV3-Large delivers an average CPU inference time of **25.38 ms** on Intel 12th/13th Gen architectures, making it virtually instantaneous to the user.
- **Uncertainty Decision Boundary:** Synthetic non-food inputs reliably yield confidence distributions under 10% (mean: 5.6%), successfully triggering the confirmation boundary.
- **Hallucination Prevention:** By supplying verified nutrient amounts directly in the system prompt context and specifying strict rules against inventing numerical values, Gemini 1.5 Flash strictly confines answers to factual ground truth.

---

## 9. Conclusion

NutriGuide AI demonstrates that high-performance AI dietary assessment does not require opaque or hallucinating black-box systems. By anchoring deep learning vision models to verified public databases and applying dense vector RAG techniques to Generative AI explanations, the application delivers reliable, transparent, and academically sound nutrition intelligence.
