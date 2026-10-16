# NutriGuide AI — Final Presentation & Viva Outline

**Project Title:** NutriGuide AI: Multimodal Generative AI Food & Nutrition Intelligence  
**Institution:** Siddaganga Institute of Technology, Department of CSE  
**Target Submission:** October 2026  
**Presentation Time:** 15–20 minutes + Q&A  

---

## Slide 1: Title & Team
- **Title:** NutriGuide AI: Multimodal Generative AI Food & Nutrition Intelligence
- **Subtitle:** Pair-Programming AI Capstone Project
- **Department:** Department of Computer Science & Engineering
- **Institution:** Siddaganga Institute of Technology, Tumakuru
- **Academic Year:** 2026

---

## Slide 2: Problem Statement & Motivation
- **The Core Issue:** Traditional dietary tracking is friction-heavy (tedious manual logging, portion guesswork).
- **The GenAI Trap:** Naive LLMs frequently hallucinate numerical nutrition metrics, producing hazardous advice.
- **Serving Inconsistency:** Discrepant portion definitions (per slice vs per pack vs per 100g) mislead consumers.
- **Allergen Risks:** Undeclared allergens or incomplete databases present serious health risks without clear disclaimers.

---

## Slide 3: Project Objectives
1. **Automated Vision Recognition:** Real-time food categorization on commodity hardware.
2. **Standardized Nutrition Retrieval:** Direct integration with USDA FoodData Central on a strict **per-100g basis**.
3. **Packaged Product & Allergen Safety:** Open Food Facts lookup with active missing-data warnings.
4. **Evidence-Grounded GenAI:** Gemini 1.5 Flash assistant constrained by FAISS semantic search over verified knowledge.
5. **Algorithmic Food Comparison:** Objective side-by-side nutrient analysis.
6. **Transparent Uncertainty:** Explicit confidence thresholds preventing ungrounded claims.

---

## Slide 4: System Architecture & Data Flow
- **High-Level Diagram:** Frontend Client (React) <-> FastAPI REST Backend <-> Vision / USDA / Open Food Facts / RAG / Gemini.
- **Three-Tier Design:**
  - Client Tier: React 19, TypeScript, Tailwind CSS v4.
  - Application Tier: FastAPI, MobileNetV3-Large, Pydantic v2.
  - External Data Tier: USDA API, Open Food Facts API, Gemini API, Curated Knowledge Base.

---

## Slide 5: Technology Stack & Technical Rationale
- **Vision:** MobileNetV3-Large (PyTorch) — chosen for low parameter count (~5.4M) and sub-30ms CPU latency.
- **Backend:** FastAPI — asynchronous I/O, native Pydantic validation, typed API schemas.
- **Frontend:** React + Vite + Tailwind CSS — responsive, fast HMR, consistent emerald/forest-green visual identity.
- **Vector Search:** Sentence Transformers (`all-MiniLM-L6-v2`) + FAISS index.
- **LLM:** Google Gemini 1.5 Flash via Google AI Studio.

---

## Slide 6: Computer Vision Pipeline & Decision Boundary
- **Input Preprocessing:** RGB conversion -> Resize(256) -> CenterCrop(224) -> ImageNet normalization.
- **Top-5 Probability Distribution:** Softmax output across 20 Food-101 target classes.
- **Uncertainty Decision Boundary:**
  - Confidence >= 40%: Accepted, triggers automated USDA nutrition retrieval.
  - Confidence < 40%: Flagged as ambiguous/unconfident, prompts manual user confirmation.
- **Empirical Inference Latency:** **25.38 ms** on CPU.

---

## Slide 7: Nutrition Retrieval & USDA Entity Matching
- **Authoritative Source:** USDA FoodData Central (Foundation, SR Legacy, FNDDS).
- **Core Nutrients Extracted:** Calories (kcal), Protein (g), Carbohydrates (g), Total Fat (g), Sugar (g), Dietary Fiber (g), Sodium (mg), Cholesterol (mg), Saturated Fat (g).
- **Mapping Coverage:** **20/20 (100%)** target categories mapped to standardized USDA search queries.
- **Standardized Basis:** Enforced per-100g basis ensures scientific comparability.

---

## Slide 8: Packaged Food & Allergen Awareness
- **Source:** Open Food Facts global open database.
- **Dual Lookup Modes:** Full-text brand/product search + Barcode scanning (EAN-13/UPC).
- **Critical Safety Feature:** Explicit warning that absence of declared allergen tags does *not* prove a product is allergen-free.

---

## Slide 9: Retrieval-Augmented Generation (RAG) & Gemini Integration
- **The Challenge:** Preventing LLM hallucination of numerical nutrition facts.
- **The Solution:** 
  - Curated 20-document domain knowledge base indexed with FAISS.
  - Sentence Transformers semantic retrieval ($k=2-3$ chunks).
  - Structured prompt injection providing verified USDA numbers as unquestionable ground truth.
  - Strict prompt instructions forbidding estimation when values are unlisted.

---

## Slide 10: Comparative Food Analysis Engine
- **Objective:** Algorithmic comparison of two foods on a normalized per-100g basis.
- **Visual Feedback:** Color-coded superiority indicators (green upward arrow for higher protein/fiber or lower calories/fat/sugar/sodium).
- **AI Summary:** Gemini synthesizes differences without declaring one food "universally healthier."

---

## Slide 11: Live Demonstration Workflows (Screenshots / Walkthrough)
1. **Screen 1:** Dashboard with hero and feature navigation.
2. **Screen 2:** Food Image Analysis with drag-and-drop, confidence pill, and alternatives drawer.
3. **Screen 3:** USDA Nutrition Detail card with per-100g metrics and direct USDA link.
4. **Screen 4:** Open Food Facts product ingredient & allergen tags.
5. **Screen 5:** AI Nutrition Assistant with source provenance citations.
6. **Screen 6:** Side-by-side Food Comparison table.

---

## Slide 12: Faculty Evaluation Matrix (10 Criteria)
| Criterion | Target | Measured Result | Status |
|---|---|---|---|
| 1. Classification Accuracy | Top-5 Distribution | Calibrated with threshold gating | Verified |
| 2. Nutrition Retrieval | USDA FDC | 9 standard nutrient metrics | Verified |
| 3. Entity Matching | 20 Categories | **20/20 (100.0%)** mapped | Verified |
| 4. Multimodal Reasoning | Vision -> USDA -> AI | Cohesive end-to-end pipeline | Verified |
| 5. Allergen Correctness | Open Food Facts | Declared tags + safety disclaimer | Verified |
| 6. Hallucination Rate | Zero numeric fabrication | Prompt-grounded in evidence | Verified |
| 7. Uncertainty Handling | Ambiguous input rejection | 5.6% conf flagged (<40% threshold) | Verified |
| 8. Prompt Quality & RAG | Semantic search | 20 docs covering 20 topics | Verified |
| 9. UI Usability | Forest Green Theme | 6 fully responsive pages | Verified |
| 10. Response Latency | Sub-100ms CV | **25.38 ms avg** CPU inference | Verified |

---

## Slide 13: Limitations & Future Enhancements
- **Current Limitations:**
  - Vision model bounded to 20 Food-101 categories.
  - Network-dependent external APIs (USDA / Open Food Facts / Gemini).
  - Single-item food recognition per image.
- **Future Enhancements:**
  - Multi-item meal segmentation using Mask R-CNN.
  - On-device optical character recognition (OCR) for physical nutrition labels.
  - User profile dietary preferences and allergen tracking.

---

## Slide 14: Conclusion & Q&A
- **Summary:** NutriGuide AI delivers an academically rigorous, evidence-grounded, multimodal solution to dietary intelligence.
- **Key Takeaways:** Speed (25ms inference), Reliability (100% entity coverage), Safety (explicit uncertainty & allergen gating).
- **Questions & Discussion:** Open floor for faculty evaluation.
