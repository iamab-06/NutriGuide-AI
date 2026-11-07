# NutriGuide AI — Academic Report Preparation Notes

**Course / Degree:** Bachelor of Engineering in Computer Science & Engineering  
**Institution:** Siddaganga Institute of Technology, Tumakuru  
**Academic Target Date:** 30 October 2026  
**Document Purpose:** Source notes, empirical tables, and section drafts for the academic final project report and viva voce presentation.

---

## 1. Abstract

Nutritional transparency is a critical determinant of public health, yet existing dietary assessment tools rely heavily on manual text logging, coarse portion estimations, or black-box generative AI chatbots prone to nutritional hallucination. This project presents **NutriGuide AI**, an end-to-end multimodal Generative AI web platform that unifies Computer Vision, authoritative nutrition databases, community packaged-food repositories, and Retrieval-Augmented Generation (RAG).

The system employs a two-tier visual recognition architecture. Primary recognition is powered by a **MobileNetV3-Large** convolutional neural network fine-tuned on a 20-class subset of the Food-101 dataset (15,000 training images, 5,000 unseen test images). The fine-tuned model achieves an empirical **90.64% Top-1 accuracy** and **97.82% Top-3 accuracy** with an average inference latency of **24.83 ms** on commodity hardware, overcoming the 2.60% baseline of untrained linear projection heads. 

To eliminate false confirmations on ambiguous or out-of-domain images, the system enforces a **70% confidence threshold** coupled with a strict **nutrition withholding policy**. Any prediction below 70% (e.g., an ambiguous 43.9% local guess) withholds definitive nutrition information (`nutrition = None`) and automatically invokes a **Google Gemini Vision multimodal fallback**. The UI presents Gemini's qualitative visual explanation alongside a one-click "Confirm & View Nutrition" button, candidate prediction selection controls, and a 20-category manual dropdown override, ensuring nutrition facts are only presented for verified foods.

Upon food identification, verified nutrient metrics (energy, protein, carbohydrates, lipids, fiber, sugar, sodium, cholesterol, saturated fat) are retrieved on a standardized **per-100g basis** from **USDA FoodData Central**. Packaged products are cross-referenced with the **Open Food Facts** API to surface verified ingredient lists and allergen tags with proactive safety disclaimers. Qualitative queries are handled by a hybrid RAG pipeline using **Sentence Transformers** (`all-MiniLM-L6-v2`) and **FAISS** vector indexing to constrain **Google Gemini**, enforcing evidence-grounded responses and eliminating fabricated numerical claims. Comprehensive testing across 37 automated tests and five end-to-end user journeys confirms 100% test pass rate, 100% USDA entity matching coverage, and robust uncertainty communication.

---

## 2. Problem Statement

Modern consumers face significant obstacles in understanding the nutritional composition and safety of the food they consume:
1. **Manual Logging Friction:** Traditional diet-tracking apps require tedious manual text entry and portion guessing, leading to low user compliance.
2. **Untrained Vision Models & Low Accuracy:** Generic or zero-shot image classifiers produce erroneous predictions (e.g., misidentifying samosas as waffles or chicken curry as ramen) when deployed without rigorous domain-specific fine-tuning.
3. **Premature Nutrition Retrieval on Uncertain Predictions:** When classifiers use loose thresholds (e.g., 40%), ambiguous predictions (like 43.9% Apple Pie for a samosa) get treated as certain, retrieving and displaying incorrect nutritional facts without user confirmation.
4. **Nutritional Hallucination in GenAI:** General-purpose Large Language Models (LLMs) frequently hallucinate numerical macro/micronutrient amounts when asked for nutritional advice, creating genuine health and safety hazards.
5. **Inconsistent Portion Reporting:** Nutrition labels alternate arbitrarily between per-serving, per-container, and per-package measurements, confounding direct nutritional comparisons.
6. **Allergen Ambiguity:** Undeclared allergens and missing product data often go uncommunicated, creating false impressions of product safety for sensitive individuals.

---

## 3. Objectives

The primary objectives of the NutriGuide AI project are:
1. **Accurate & Rapid Visual Recognition:** Fine-tune MobileNetV3-Large on 20 canonical food categories, achieving >90% Top-1 accuracy with sub-30ms inference latency.
2. **Multimodal Fallback & Responsible Uncertainty:** Implement strict confidence thresholding (70% cutoff) with automatic Gemini Vision multimodal fallback, withholding unconfirmed nutrition, and offering candidate selection buttons and manual category overrides.
3. **Grounded Empirical Retrieval:** Build an API pipeline interfacing with USDA FoodData Central to extract standardized, unadulterated nutrient profiles on a per-100g basis.
4. **Packaged Product Intelligence:** Integrate Open Food Facts to deliver ingredient and allergen transparency with explicit missing-field notices.
5. **Hallucination-Proof AI Assistant:** Construct a RAG pipeline utilizing FAISS vector retrieval coupled with strict prompt boundaries to guide Gemini in explaining nutrition facts without inventing numbers.
6. **Standardized Food Comparison:** Enable side-by-side per-100g comparison of foods with algorithmic superiority detection.

---

## 4. Proposed Methodology & Architecture

```
[Food Image Input] ──> [MobileNetV3 Inference (24.83 ms)]
                              │
                              ▼
                  [Confidence Check (>= 70%)]
                              │
         ┌────────────────────┴────────────────────┐
         ▼                                         ▼
   [Pass: Confident (>= 70%)]            [Fail: Uncertain (< 70%)]
         │                                         │
   [USDA Entity Normalization]           [Gemini Vision Multimodal Fallback]
         │                                         │
   [Per-100g Nutrient Fetch]             [Definitive Nutrition Withheld (None)]
         │                                         │
         │                               [Prompt User Confirmation: Gemini Button,
         │                                Candidate Selectors, Manual Dropdown]
         │                                         │
         │                               [User Confirms Food Identity]
         │                                         │
         │                               [Per-100g Nutrient Fetch for Confirmed Food]
         │                                         │
         └────────────────────┬────────────────────┘
                              ▼
                   [Direct UI Rendering]
                 [NutritionCard Component]
                              │
                              ▼
                  [RAG Knowledge Pipeline]
                 [Sentence Transformers (384-d)]
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
| **Frontend Framework** | React 19 + TypeScript | Vue, Angular | Robust typing, component reusability, widespread industry adoption. |
| **Build & Styling** | Vite 8 + Tailwind CSS v4 | Webpack, plain CSS | Instant HMR, minimal bundle footprint (384 KB JS, 37 KB CSS), utility design system. |
| **Backend Framework** | FastAPI + Python 3.12 | Flask, Django, Node.js | Native asynchronous I/O, automatic OpenAPI schema generation, Pydantic type safety. |
| **Vision Backbone** | MobileNetV3-Large | ResNet-50, ViT-Base | Optimal parameter efficiency (~5.4M params), 24.83 ms latency, easily runs on edge/CPU. |
| **Multimodal Fallback** | Google Gemini Vision | Local BLIP-2, LLaVA | High-quality visual understanding for ambiguous images without hosting multi-gigabyte models locally. |
| **Primary Data Source** | USDA FoodData Central | Nutritionix, Edamam | Authoritative public scientific reference data, transparent nutrient IDs, no proprietary lock-in. |
| **Product Data Source** | Open Food Facts | Spoonacular | Open collaborative global dataset, open barcode resolution, detailed allergen tags. |
| **Vector Indexing** | FAISS + Sentence Transformers | ChromaDB, Pinecone | In-process, zero cloud infrastructure cost, fast dense vector search on CPU. |
| **Generative LLM** | Google Gemini (`gemini-3.5-flash`) | Local Llama 3, GPT-4 | Native multimodal support, low latency (~2.0s), multi-candidate quota resilience. |

---

## 6. Dataset Descriptions & Data Provenance

1. **Food-101 Subset (Computer Vision):**
   - Source: Computer Vision Laboratory, ETH Zurich.
   - Target Classes (20): Apple Pie, Caesar Salad, Chicken Curry, Chocolate Cake, Donuts, French Fries, Fried Rice, Hamburger, Hot Dog, Ice Cream, Omelette, Pancakes, Pizza, Ramen, Samosa, Spaghetti Bolognese, Spring Rolls, Steak, Sushi, Waffles.
   - Split Structure:
     - Training: 15,000 images (750 per class) strictly from the official Food-101 train split.
     - Validation/Testing: 5,000 images (250 per class) strictly from the official Food-101 test split.
     - Data Leakage: Verified 0% train/test leakage.
2. **USDA FoodData Central:**
   - Source: U.S. Department of Agriculture, Agricultural Research Service.
   - Datasets queried: Foundation Foods, National Nutrient Database for Standard Reference (SR Legacy), Food and Nutrient Database for Dietary Studies (FNDDS).
3. **Open Food Facts Database:**
   - Source: Open Food Facts non-profit open database (ODbL).
   - Fields extracted: Ingredients list, allergen categories, brand owner, barcode.
4. **NutriGuide Curated Nutrition Knowledge Base:**
   - 20 verified reference texts covering macronutrient metabolism, dietary fiber, glycemic index, major food allergens (US/EU definitions), and food-specific nutritional profiles.

---

## 7. Experimental Results & Discussion

### 7.1 Food Classification Accuracy Comparison

| Evaluation Metric | Baseline (Untrained Head) | Fine-Tuned MobileNetV3-Large | Absolute Improvement |
|---|---|---|---|
| **Top-1 Accuracy** | 2.60% (13 / 500) | **90.64% (4,532 / 5,000)** | **+88.04%** |
| **Top-3 Accuracy** | 10.20% (51 / 500) | **97.82% (4,891 / 5,000)** | **+87.62%** |
| **Training Accuracy** | N/A | **99.31%** (Epoch 10) | N/A |
| **Training Loss** | N/A | **0.0275** | Converged |
| **Model Weights Checkpoint** | Missing | `nutriguide_classifier.pth` (17.1 MB) | Verified |

#### Per-Class Accuracy Highlights (Fine-Tuned Model on Unseen Images):
- **Samosa:** 98.4% (246 / 250)
- **Sushi:** 96.8% (242 / 250)
- **Pizza:** 94.0% (235 / 250)
- **Hamburger:** 92.4% (231 / 250)
- **Fried Rice:** 91.2% (228 / 250)
- **Omelette:** 93.6% (234 / 250)
- **Pancakes:** 91.6% (229 / 250)
- **Waffles:** 89.2% (223 / 250)

### 7.2 System Benchmark Measurements (`benchmark.py`)
- **Classification Latency:** **24.83 ms average** (Min: 24.03 ms, Max: 26.47 ms).
- **USDA Entity Matching Coverage:** **20/20 (100.0%)** across all supported categories.
- **Uncertainty Rejection Compliance:** Synthetic flat non-food images generate low confidence (16.4% on gray, 18.7% on flat color), correctly triggering the `< 70%` uncertainty policy.
- **RAG Knowledge Base:** 20 documents covering 20 distinct nutrition topics.

### 7.3 Automated Test Suite Verification
- **Total Tests:** 37 tests across 9 test suites.
- **Pass Rate:** **37 / 37 (100% pass rate)** in 80.46s.
- **Suites:** Classifier (3/3), Compare (2/2), Food Identification & Fallback (6/6), Gemini (11/11), Health (2/2), Nutrition (3/3), Products (3/3), RAG (2/2), Vision Improvements (5/5).

### 7.4 End-to-End User Journey Verification
- All 5 core user journeys verified end-to-end through the Vite proxy (`http://localhost:5173`):
  1. Nutrition search: 200 OK (pizza -> 266 kcal).
  2. Product search: 200 OK (Nutella -> allergens milk, nuts, soybeans).
  3. AI Assistant: 200 OK (fried rice macros grounded with 163 kcal, 28g carbs, 5.2g protein, 3.5g fat).
  4. Compare Foods: 200 OK (pizza vs hamburger per-100g normalized comparison).
  5. Analyze Food: 200 OK (image upload, MobileNetV3 inference, Gemini Vision fallback, nutrition withheld until confirmation, candidate selection).

---

## 8. Conclusion

NutriGuide AI demonstrates that high-performance AI dietary assessment does not require opaque or hallucinating black-box systems. By anchoring deep learning vision models (fine-tuned MobileNetV3-Large reaching 90.64% Top-1 accuracy) to verified public databases (USDA FoodData Central and Open Food Facts) and applying dense vector RAG techniques to Generative AI explanations, the application delivers reliable, transparent, and academically sound nutrition intelligence.
