# NutriGuide AI — Presentation Outline (18-Slide Master Plan)

**Project Title:** NutriGuide AI: A Multimodal Food Recognition and Nutrition Analysis Assistant  
**Institution:** Department of Computer Science and Engineering, Siddaganga Institute of Technology, Tumakuru  
**Academic Target:** Final Capstone Presentation & Defense (2026)  
**Estimated Time:** 15–20 Minutes (+ 10 Minutes Q&A)  

---

## Slide 1: Title & Academic Affiliation
- **Title:** NutriGuide AI: A Multimodal Food Recognition and Nutrition Analysis Assistant
- **Department:** Department of Computer Science and Engineering
- **Institution:** Siddaganga Institute of Technology, Tumakuru, Karnataka
- **Academic Year:** 2026
- **Presenter Notes:** Introduce the project title, team members, faculty guides, and the overarching mission: bringing scientific accuracy, speed, and safety to everyday dietary awareness.

---

## Slide 2: Problem Statement & Motivation
- **Key Points:**
  - Friction in food logging: Manual text entry leads to a 70%+ user abandonment rate.
  - Opaque packaged food ingredients: Microscopic labels and undeclared allergens create health risks.
  - The Generative AI trap: Naive LLMs frequently hallucinate numerical dietary values and daily allowances.
  - Computer vision fragility: Models arbitrarily accept incorrect food categories without notifying users of visual uncertainty.
- **Suggested Visual:** Contrast diagram showing manual text search vs. instant camera recognition, paired with an example of LLM hallucination.
- **Presenter Notes:** Emphasize that dietary tracking is fundamentally broken between high manual effort on one end and dangerous AI hallucinations on the other.

---

## Slide 3: Project Objectives
- **Key Points:**
  1. Low-latency food recognition ($\le 50\text{ ms}$, $\ge 85\%$ accuracy) on commodity CPU hardware.
  2. Calibrated uncertainty gating (70% threshold) with automatic Gemini Vision multimodal fallback.
  3. Authoritative nutritional extraction via USDA FoodData Central normalized per 100 grams.
  4. Ingredient transparency and declared allergen extraction via Open Food Facts.
  5. Evidence-grounded conversational reasoning using Sentence Transformers and FAISS RAG.
  6. Clean, responsive web interface adhering to the approved forest-green and white design system.
- **Suggested Visual:** High-level icon map highlighting the six core pillars.
- **Presenter Notes:** State clearly that our objective is not just to build a model, but a complete, reliable, verified end-to-end full-stack dietary intelligence system.

---

## Slide 4: System Architecture Overview
- **Key Points:**
  - Three-tier decoupled architecture: Presentation (React 19 + TypeScript), Application (FastAPI + Uvicorn), and Data/Intelligence Tier.
  - High-performance asynchronous microservice routing with 6 modular endpoints.
  - Multi-tier fallback design ensuring 100% availability even during upstream cloud outages.
- **Suggested Visual:** Mermaid flowchart from `docs/diagrams/system_architecture.mmd`.
- **Presenter Notes:** Walk the evaluation committee through client-to-server data flow, emphasizing the clean separation of concerns and reverse proxy architecture.

---

## Slide 5: Technology Stack & Justification
- **Key Points:**
  - **Frontend:** React 19, TypeScript, Vite 8, Tailwind CSS v4, Lucide React, Axios.
  - **Backend:** FastAPI, Python 3.12, Uvicorn, Pydantic v2, HTTPX.
  - **Deep Learning:** PyTorch, Torchvision, MobileNetV3-Large (`nutriguide_classifier.pth`, 17.1 MB).
  - **Generative AI & RAG:** Google Gemini 1.5/2.x Flash, Sentence Transformers (`all-MiniLM-L6-v2`), FAISS CPU (`IndexFlatL2`).
  - **Data Endpoints:** USDA FoodData Central, Open Food Facts REST API.
- **Suggested Visual:** Technology logo grid organized by frontend, backend, ML/AI, and external APIs.
- **Presenter Notes:** Justify why MobileNetV3-Large was chosen over heavy ResNet models, and why FastAPI was chosen over Flask for native asynchronous concurrency.

---

## Slide 6: Dataset & Split Protocol (Food-101)
- **Key Points:**
  - Benchmark source: ETH Zurich Food-101 dataset.
  - Selected 20 diverse, representative food classes (Samosa, Pizza, Sushi, Chicken Curry, etc.).
  - Training set: Exactly 15,000 images (750 per class).
  - Validation/Test set: Exactly 5,000 unseen images (250 per class).
  - Strict zero-leakage protocol: Verified mutually disjoint train and test splits.
- **Suggested Visual:** Sample grid showing the 20 food categories.
- **Presenter Notes:** Highlight that evaluation was conducted strictly on unseen test images, ensuring reported metrics represent genuine real-world generalization.

---

## Slide 7: Computer Vision Pipeline (MobileNetV3-Large)
- **Key Points:**
  - Preprocessing: RGB conversion $\to$ `Resize(256)` $\to$ `CenterCrop(224)` $\to$ ImageNet normalization ($\mu, \sigma$).
  - Linear classification head: 960 bottleneck features $\to$ 20 food classes.
  - Softmax probability vector outputs Top-5 ranked candidate predictions.
  - Benchmarked classification latency: **24.83 ms** average per image on standard CPU.
- **Suggested Visual:** Diagram from `docs/diagrams/food_recognition_pipeline.mmd`.
- **Presenter Notes:** Explain the mathematics of depthwise separable convolutions and how they achieve sub-30ms execution on standard computers.

---

## Slide 8: Baseline Audit vs. Fine-Tuned Accuracy
- **Key Points:**
  - Baseline audit discovery: Untrained classification head achieved only **2.60% Top-1** accuracy.
  - Fine-tuning breakthrough: 10 epochs on Food-101 achieved **90.64% Top-1** and **97.82% Top-3** accuracy (+88.04% gain).
  - High-performing classes: Samosa (98.4%), Sushi (96.8%), Pizza (94.0%), Hamburger (92.4%).
- **Suggested Visual:** Comparison bar chart showing 2.60% vs. 90.64% Top-1 accuracy, and validation loss convergence curve over 10 epochs.
- **Presenter Notes:** Share the honest story of our audit: we identified that early checkpoints lacked fine-tuned weights, implemented `train_food20.py`, and systematically proved a 90.64% accuracy level.

---

## Slide 9: Uncertainty Gating & The 70% Decision Boundary
- **Key Points:**
  - Why Softmax confidence does not equal real-world accuracy: Overconfidence on ambiguous inputs.
  - Calibration: Raised threshold from naive 40% to **70%** (`CONFIDENCE_THRESHOLD = 0.70`).
  - Predictions $\ge 70\%$: Accepted directly with automated USDA lookup.
  - Predictions $< 70\%$: Flagged as ambiguous, triggering Gemini Vision fallback.
- **Suggested Visual:** Threshold bifurcation chart illustrating direct acceptance vs. fallback triggering.
- **Presenter Notes:** Explain the samosa case study: an ambiguous samosa scored 43.9% for Apple Pie; our 70% threshold rejected it, preventing false dietary advice.

---

## Slide 10: Multimodal Gemini Vision Fallback & Confirmation Flow
- **Key Points:**
  - Fallback engine: Ingests raw image bytes into Google Gemini Vision (`gemini-3.5-flash`).
  - Strict Safety Mandate: **Definitive nutrition is strictly withheld (`nutrition = None`)** until user confirms.
  - Interactive User Recovery: One-click "Confirm & View Nutrition" button, top-5 alternative chips, and 20-category manual dropdown.
- **Suggested Visual:** Sequence diagram from `docs/diagrams/gemini_vision_fallback.mmd`.
- **Presenter Notes:** Emphasize our user-in-the-loop safety philosophy: AI recommends, but the user always retains the final confirmation before nutrition is retrieved.

---

## Slide 11: Standardized Nutrition Extraction (USDA FoodData Central)
- **Key Points:**
  - Direct integration with USDA FoodData Central REST API.
  - Standardized **per-100g basis** eliminates conflicting serving-size definitions.
  - 9 core nutrient IDs extracted: Calories, Protein, Carbs, Fat, Sugar, Fiber, Sodium, Cholesterol, Saturated Fat.
  - 100% entity coverage across all 20 categories.
  - Automatic fallback to verified local USDA Standard Reference dataset during rate limits or network outages.
- **Suggested Visual:** Screenshot of verified `NutritionCard` component showing per-100g breakdown and USDA hyperlink.
- **Presenter Notes:** Point out that our personal USDA API key is configured and verified, returning 10 real hits for queries like "pizza".

---

## Slide 12: Packaged Food Telemetry & Allergen Safety (Open Food Facts)
- **Key Points:**
  - Dual lookup modes: Product name search and EAN-13/UPC barcode scanning.
  - Multi-host resilience: Automatic failover between `world.openfoodfacts.net` and `world.openfoodfacts.org`.
  - Allergen safety alert: Explicit notice that absence of declared tags does *not* prove a product is allergen-free.
- **Suggested Visual:** Screenshot of `IngredientsAllergens` page showing Nutella search results, barcode display, and allergen tags (`milk, nuts, soybeans`).
- **Presenter Notes:** Explain why the allergen absence disclaimer is vital for consumer safety.

---

## Slide 13: Retrieval-Augmented Generation (RAG) Architecture
- **Key Points:**
  - Problem: Eliminating LLM numerical hallucination in dietary advice.
  - Solution: 20 curated domain knowledge documents embedded with `all-MiniLM-L6-v2` (384 dimensions).
  - In-memory vector store: `FAISS IndexFlatL2` for sub-millisecond semantic similarity search ($k=2$).
  - Food Entity Auto-Grounding: Automatically queries USDA for detected foods and injects verified numbers into Gemini prompt context.
- **Suggested Visual:** Flowchart from `docs/diagrams/rag_pipeline.mmd`.
- **Presenter Notes:** Explain how our auto-grounding mechanism guarantees that whenever a user asks about "fried rice", exact USDA numbers are provided to the LLM as ground truth.

---

## Slide 14: Objective Food Comparison Engine
- **Key Points:**
  - Side-by-side algorithmic nutrient comparison of two foods normalized per 100g.
  - Visual superiority indicators highlighting advantageous nutrient profiles.
  - Automated AI dietary synthesis generated via Gemini explaining contextual trade-offs without declaring one food "universally superior."
- **Suggested Visual:** Side-by-side comparison table of Pizza vs. Hamburger.
- **Presenter Notes:** Demonstrate how side-by-side per-100g normalization helps users make objective, evidence-based meal choices.

---

## Slide 15: Security, Privacy & Defensive Ingestion
- **Key Points:**
  - Complete API key isolation: Keys stored in `.env` and masked as `"***"` in logs and strings.
  - Ingestion defense: Client and backend MIME checks (JPEG/PNG/WebP) and 10 MB upload cap.
  - Polyglot payload prevention: Ingested images are re-encoded to RGB pixels via Pillow, stripping EXIF and malicious metadata.
  - Stateless architecture: No user meal photos or biometric data are stored on disk.
- **Suggested Visual:** Security architecture diagram showing client checks, CORS whitelist, payload limiters, and secret masking.
- **Presenter Notes:** Reassure the committee that API keys are never exposed in client bundles or public repositories.

---

## Slide 16: Verification, Automated Testing & Benchmarks
- **Key Points:**
  - Backend test suite: **37 / 37 tests passed (100% pass rate)** in 71.18s across 9 test modules.
  - Classification latency: **24.83 ms** average on CPU.
  - End-to-end user journeys: All 5 core journeys verified through Vite proxy.
  - Frontend production build: Built in **1.20s** with zero errors.
- **Suggested Visual:** Console screenshot of `pytest -v` passing 37/37 tests and `npm run build` passing.
- **Presenter Notes:** Emphasize that all claimed features have been verified by reproducible automated test suites.

---

## Slide 17: Limitations & Future Roadmap
- **Key Points:**
  - Current boundaries: 20 food categories, 2D visual classification (no 3D volume/weight estimation), single-session chat memory.
  - Future milestones:
    - Phase 1 (6 Months): Expand classifier to 101 categories using YOLOv11 for multi-item bounding boxes.
    - Phase 2 (12 Months): Monocular depth estimation (MiDaS/Depth Anything) for 3D volumetric mass calculation.
    - Phase 3 (24 Months): Continuous glucose monitor (CGM) integration and browser-native edge inference via WebGPU / ONNX Web.
- **Suggested Visual:** 3-Phase evolution roadmap flowchart from `docs/LIMITATIONS_AND_FUTURE_SCOPE.md`.
- **Presenter Notes:** Demonstrate clear academic and engineering vision for scaling the system into a clinical-grade platform.

---

## Slide 18: Conclusion & Summary
- **Key Points:**
  - Delivered an end-to-end multimodal dietary intelligence system combining edge vision, verified USDA data, Open Food Facts, and FAISS RAG.
  - Solved food recognition inaccuracy: 90.64% Top-1, 97.82% Top-3 accuracy with sub-25ms latency.
  - Enforced ethical AI safety: 70% confidence threshold, Gemini Vision fallback, and strict nutrition withholding on unconfirmed dishes.
  - Fully tested and verified across 37 automated test cases and production builds.
- **Presenter Notes:** Thank the examination committee, faculty advisors, and open the floor for technical questions and live demonstration.
