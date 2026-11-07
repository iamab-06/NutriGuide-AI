# NutriGuide AI — Project Abstract

**Project Title:** NutriGuide AI: A Multimodal Food Recognition, Nutrition Analysis, and Ingredient Awareness Assistant  
**Institution:** Department of Computer Science and Engineering, Siddaganga Institute of Technology, Tumakuru, Karnataka  
**Academic Year:** 2026  

---

## Abstract

Nutritional awareness is a primary determinant of preventive healthcare, chronic illness mitigation, and dietary wellness. However, contemporary consumers encounter significant friction in accurately determining the caloric and nutritional composition of meals, decoding complex ingredient formulations, identifying hidden allergens, and acquiring reliable, hallucination-free dietary intelligence. Traditional nutritional tracking applications depend heavily on tedious manual logging, unverified user-submitted food databases, and generic advice lacking scientific grounding.

To address these limitations, this project presents **NutriGuide AI**, an end-to-end multimodal artificial intelligence system that unifies Computer Vision, authoritative nutritional databases, open-source packaged food telemetry, and vector-grounded Large Language Model (LLM) reasoning into a responsive full-stack web application.

The core computer vision pipeline employs a fine-tuned **MobileNetV3-Large** deep convolutional neural network trained on a 20-category subset of the benchmark **Food-101** dataset (15,000 training images, 5,000 validation images). Empirical evaluation demonstrates that the fine-tuned architecture achieves **90.64% Top-1 accuracy** and **97.82% Top-3 accuracy** with an average inference latency of **24.83 ms** on commodity hardware, representing an 88.04% absolute improvement over baseline untrained classification heads.

To address real-world visual ambiguity (e.g., cross-class food similarities), NutriGuide AI implements a calibrated **70% confidence threshold gating policy**. Ambiguous predictions ($< 70\%$) automatically trigger a secondary **Google Gemini Vision multimodal fallback**. Crucially, the system enforces a strict safety protocol: definitive nutritional information is withheld until the user confirms the dish identity via one-click recommendation acceptance, ranked alternative candidate selection, or manual 20-category dropdown override, eliminating false dietary guidance.

For verified food items, the backend queries **USDA FoodData Central** to retrieve standardized macro- and micronutrient quantities normalized per 100 grams. For commercial packaged products, the system integrates the **Open Food Facts API**, enabling name search and EAN-13 barcode lookups to extract ingredient hierarchies and declared allergens with prominent safety disclaimers regarding unlisted allergens.

To deliver conversational guidance without numerical hallucination, NutriGuide AI implements a **Retrieval-Augmented Generation (RAG)** architecture. A curated 20-topic nutrition knowledge base is vectorized using **Sentence Transformers (`all-MiniLM-L6-v2`)** and indexed with **FAISS (Facebook AI Similarity Search)**. The system dynamically binds retrieved scientific context and verified USDA data into structured prompts executed via **Google Gemini 1.5/2.x Flash** with gRPC thread isolation, ensuring verifiable attribution and preventing unsubstantiated medical claims.

The user interface is engineered with **React 19, TypeScript, and Vite 8**, styled with Tailwind CSS in an approved forest-green and white aesthetic (`#0d2818`, `#2d6a4f`, `#52b788`). Automated verification across 37 backend test cases, end-to-end user journeys, and production bundle builds confirms that NutriGuide AI provides a dependable, transparent, and computationally efficient foundation for intelligent dietary awareness.

**Keywords:** Computer Vision, MobileNetV3-Large, Food Classification, Multimodal Fallback, Gemini Vision, USDA FoodData Central, Open Food Facts, Retrieval-Augmented Generation (RAG), FAISS, FastAPI, React, TypeScript.
