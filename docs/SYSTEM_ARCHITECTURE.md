# NutriGuide AI — Comprehensive System Architecture Specification

**Project Title:** NutriGuide AI: Multimodal Food Recognition and Nutrition Analysis Assistant  
**Institution:** Siddaganga Institute of Technology, Department of Computer Science & Engineering  
**System Classification:** Multimodal AI Full-Stack Web Application  
**Document Version:** 1.0 (Production Release)  

---

## 1. Architectural Philosophy & Overview

NutriGuide AI adheres to a modern, decoupled three-tier architectural paradigm designed for low-latency inference, fault tolerance, and evidence-grounded AI responses:

1. **Presentation Tier (Frontend):** A responsive Single Page Application (SPA) built using React 19, TypeScript, and Tailwind CSS v4, bundled with Vite 8.
2. **Application Server Tier (Backend):** An asynchronous Python 3.12 microservice powered by FastAPI and Uvicorn, managing computer vision inference, vector retrieval, and external API orchestration.
3. **Data & Intelligence Tier (External & Embedded):** A hybrid fabric comprising local fine-tuned PyTorch checkpoints, local FAISS vector indices, verified USDA fallback tables, local Gemma 3 4B IT multimodal LLM via Ollama, and live external APIs (USDA FoodData Central, Open Food Facts).

```mermaid
flowchart TD
    subgraph Client["Client Presentation Tier (React 19 + TypeScript + Vite 8)"]
        User(["Client Browser"])
        App["App Router (App.tsx)"]
        Layout["Shared Layout Shell (Layout.tsx)"]
        
        P_Dash["Dashboard (/)]
        P_Analyze["Analyze Food (/analyze)"]
        P_Nutr["Nutrition Info (/nutrition)"]
        P_Allergen["Ingredients & Allergens (/ingredients)"]
        P_Assistant["AI Assistant (/assistant)"]
        P_Compare["Compare Foods (/compare)"]
        
        APIModule["API Client (api.ts - Axios)"]
    end

    subgraph ReverseProxy["Development Gateway (:5173)"]
        ViteDev["Vite Reverse Proxy (/api/* -> :8000/api/*)"]
    end

    subgraph ServerTier["Application Server Tier (FastAPI + Python 3.12 on :8000)"]
        MainApp["ASGI Main App (main.py)"]
        CORSMiddleware["CORS Middleware"]
        ConfigManager["Settings Manager (config.py - Pydantic)"]
        
        R_Health["/api/health"]
        R_Analyze["/api/analyze"]
        R_Nutr["/api/nutrition"]
        R_Prod["/api/products"]
        R_Chat["/api/chat"]
        R_Comp["/api/compare"]
    end

    subgraph VisionPipeline["Vision & Multimodal Subsystem"]
        TorchPipe["Torchvision Transform Pipeline"]
        MobileNet["MobileNetV3-Large (nutriguide_classifier.pth)"]
        Gate{"Confidence >= 70%?"}
        GeminiVision["Local Vision Fallback (classify_food_with_vision)"]
    end

    subgraph DataAndRAG["Nutrition & RAG Intelligence"]
        USDASvc["USDA Service (nutrition.py)"]
        OFFSvc["Open Food Facts Service (openfoodfacts.py)"]
        RAGSvc["RAG Service (rag_service.py)"]
        OllamaSvc["Ollama Service (ollama_service.py)"]
        
        FAISSIdx[("FAISS L2 Flat Index")]
        SentenceModel["all-MiniLM-L6-v2 Embedder"]
        KBStore[("Curated Nutrition KB (20 Docs)")]
        USDARef[("USDA Standard Reference Fallback")]
    end

    subgraph LocalLLM["Local Multimodal LLM"]
        OllamaDaemon["Ollama Server (http://localhost:11434)"]
        Gemma3["Google Gemma 3 4B IT (gemma3:4b)"]
    end

    subgraph CloudAPIs["External Authoritative APIs"]
        LiveUSDA["USDA FoodData Central API"]
        LiveOFF["Open Food Facts REST API"]
    end

    User <--> App
    App --> Layout
    Layout --> P_Dash & P_Analyze & P_Nutr & P_Allergen & P_Assistant & P_Compare
    P_Dash & P_Analyze & P_Nutr & P_Allergen & P_Assistant & P_Compare --> APIModule
    APIModule <--> ViteDev
    ViteDev <--> MainApp

    MainApp --> CORSMiddleware --> ConfigManager
    MainApp --> R_Health & R_Analyze & R_Nutr & R_Prod & R_Chat & R_Comp

    R_Analyze --> TorchPipe --> MobileNet --> Gate
    Gate -- ">= 70% (Confident)" --> USDASvc
    Gate -- "< 70% (Uncertain)" --> GeminiVision
    GeminiVision <--> OllamaDaemon

    R_Nutr --> USDASvc
    R_Prod --> OFFSvc
    R_Comp --> USDASvc & OllamaSvc
    R_Chat --> RAGSvc & OllamaSvc

    RAGSvc --> SentenceModel --> FAISSIdx
    KBStore -.-> FAISSIdx

    USDASvc <--> LiveUSDA
    USDASvc -. "Rate Limit / Timeout" .-> USDARef
    OFFSvc <--> LiveOFF
    OllamaSvc <--> OllamaDaemon --> Gemma3
```

---

## 2. Frontend Subsystem Architecture (`frontend/src/`)

### 2.1 Component Hierarchy & Routing
The frontend employs **React Router v7** with clean client-side routing:
- **`Layout.tsx`**: Global responsive container featuring a collapsible dark forest-green sidebar (`#0d2818`) with emerald active indicators (`#52b788`), mobile menu drawer, and top navigation bar.
- **`Dashboard.tsx`**: High-level launchpad with key performance indicators (20 Food Categories, USDA FoodData Central, Gemma 3 4B + RAG Pipeline) and quick action cards for the five main features.
- **`AnalyzeFood.tsx`**: Multimodal visual analyzer featuring drag-and-drop file ingestion, client-side MIME/size validation, candidate prediction buttons, manual 20-category dropdown override, Gemma 3 Vision recommendation display, and strict nutrition withholding until user confirmation.
- **`NutritionInfo.tsx`**: Real-time food query interface displaying verified per-100g nutritional breakdowns from USDA FoodData Central with calorie callouts and macronutrient pill badges.
- **`IngredientsAllergens.tsx`**: Dual-mode product explorer (full-text search and EAN-13 barcode lookup) connecting to Open Food Facts, extracting ingredients, declared allergens, and safety flags.
- **`AIAssistant.tsx`**: Evidence-grounded conversational assistant featuring instant quick prompts, scrollable message history, provenance badges, and thread safety powered by local Gemma 3 4B IT.
- **`CompareFoods.tsx`**: Side-by-side comparative nutritional matrix with dynamic superiority indicators across calories, protein, carbs, and fat, paired with automated AI comparison narratives.

### 2.2 Reusable Atomic UI Components
- **`NutritionCard.tsx`**: Renders standardized per-100g nutritional metrics (calories, protein, carbohydrates, total fat, sugar, dietary fiber, sodium, cholesterol, saturated fat) with direct hyperlinks to USDA FDC records.
- **`ConfidenceBadge.tsx`**: Visual certainty indicator (Green $\ge 75\%$, Blue $70-74\%$, Amber $< 70\%$).
- **`LoadingSpinner.tsx`**: Branded SVG spinner with accessibility labels.
- **`ErrorMessage.tsx`**: Standardized error card with retry callbacks and error message normalization.

---

## 3. Backend Subsystem Architecture (`backend/app/`)

### 3.1 Routing & API Layer (`app/api/`)
- **`/api/health`**: Returns application status, version, and running environment metadata.
- **`/api/categories`**: Lists all 20 supported Food-101 categories with canonical keys and human-readable display names.
- **`/api/analyze`**: Accepts multipart image uploads, executes MobileNetV3-Large classification, evaluates the 70% confidence threshold, triggers local Gemma 3 Vision fallback when uncertain, and returns structured predictions.
- **`/api/nutrition/{food_name}`**: Retrieves verified macro- and micronutrient records from USDA FoodData Central, mapping queries to foundation data or local standard reference fallbacks.
- **`/api/products/search` & `/api/products/barcode/{code}`**: Queries Open Food Facts for packaged goods, parsing declared allergen tags and ingredient hierarchies.
- **`/api/chat`**: Auto-detects food entities, retrieves FAISS vector context, compiles structured prompts, and queries local Gemma 3 4B IT via Ollama.
- **`/api/compare`**: Normalizes two distinct food items per 100g, generates comparison notes, and prompts Gemma 3 4B IT for comparative dietary insights.

---

## 4. Machine Learning & Vision Architecture

### 4.1 Fine-Tuned MobileNetV3-Large
- **Backbone Architecture:** MobileNetV3-Large pretrained on ImageNet-1k (V2). Combines depthwise separable convolutions with inverted residual bottlenecks and squeeze-and-excitation optimization blocks.
- **Classification Head:** Linear projection layer mapping 960 bottleneck features to 20 target classes ($960 \to 20$).
- **Checkpoint Location:** `backend/models/nutriguide_classifier.pth` (17.1 MB), loaded securely with `weights_only=True`.
- **Inference Preprocessing Pipeline:**
  $$\text{Image} \xrightarrow{\text{RGB}} \text{Resize}(256) \xrightarrow{} \text{CenterCrop}(224) \xrightarrow{} \text{ToTensor}() \xrightarrow{} \text{Normalize}(\mu, \sigma) \xrightarrow{} \text{Softmax}(\mathbf{z})$$
  Where ImageNet normalization parameters are:
  $$\mu = [0.485, 0.456, 0.406], \quad \sigma = [0.229, 0.224, 0.225]$$
- **Empirical Accuracy:** **90.64% Top-1** and **97.82% Top-3** evaluated on 5,000 unseen test images (250 per class).
- **Latency:** **24.83 ms** average per image on standard CPU.

### 4.2 Confidence Threshold Gating & Multimodal Vision Fallback
```text
IF max_class_probability >= 0.70:
    is_confident = True
    requires_confirmation = False
    Fetch USDA nutrition directly
ELSE:
    is_confident = False
    requires_confirmation = True
    nutrition = None  (STRICT WITHHOLDING POLICY)
    Invoke Gemma 3 4B IT Multimodal Vision Fallback (Ollama)
    Present recommendation to user for one-click confirmation
```

---

## 5. Retrieval-Augmented Generation (RAG) Architecture

### 5.1 Vector Store & Embeddings
- **Embedding Model:** `sentence-transformers/all-MiniLM-L6-v2` (384-dimensional dense semantic vectors).
- **Vector Database:** `faiss.IndexFlatL2` (exact $L_2$ Euclidean distance nearest-neighbor search).
- **Curated Knowledge Base:** 20 nutrition documents covering macronutrient metabolism, dietary fiber, glycemic index, major food allergens (milk, eggs, peanuts, tree nuts, wheat, soy, fish, shellfish), hydration, and specific food category profiles.

### 5.2 Auto-Grounding & Context Injection
1. **Entity Extraction:** When a user asks a question (e.g., *"How much protein is in chicken curry?"*), regex pattern matching extracts the food entity.
2. **Deterministic Data Binding:** The backend automatically queries USDA FoodData Central for the detected food and injects exact numerical ground truth into the prompt context.
3. **Semantic Retrieval:** The query is embedded via `all-MiniLM-L6-v2`, and the FAISS index retrieves the top-2 most relevant domain knowledge chunks ($k=2$).
4. **Prompt Strictness:** The system instruction explicitly prohibits guessing unlisted numbers, requiring the model to cite the provided evidence or state that the value is unrecorded.

---

## 6. Security, Privacy & Configuration Architecture

- **Zero Secret Exposure:** Credentials (`GEMINI_API_KEY`, `USDA_API_KEY`) are stored exclusively in `backend/.env` and excluded from Git tracking via `.gitignore`.
- **String Masking:** `Settings.__repr__` masks keys as `***` to guarantee secrets are never printed to console logs, error traces, or test outputs.
- **Upload Hardening:** Ingestion endpoints enforce strict MIME type checks (JPEG, PNG, WebP) and a 10 MB payload cap to prevent Denial-of-Service (DoS) attacks.
- **Failover & Resilience:** USDA search incorporates automatic fallback to local verified USDA Reference Data during upstream network outages or rate limiting.
