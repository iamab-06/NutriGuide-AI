# NutriGuide AI — Technology Stack & Architectural Justification

**Project:** NutriGuide AI  
**Institution:** Department of Computer Science and Engineering, Siddaganga Institute of Technology  
**Academic Year:** 2026  

---

## 1. Complete Technology Inventory

| Layer / Subsystem | Technology | Version | Location / Usage | Primary Purpose |
|---|---|---|---|---|
| **Frontend Framework** | React | `^19.0.0` | `frontend/src/` | Component-based interactive Single Page Application |
| **Language (Frontend)** | TypeScript | `~5.7.2` | `frontend/src/` | Type-safe client code and data contract enforcement |
| **Build Tool & Bundler** | Vite | `^8.3.4` | `frontend/vite.config.ts` | High-speed HMR development server and production bundler |
| **Styling Framework** | Tailwind CSS | `^4.0.0` | `frontend/src/index.css` | Utility-first responsive design adhering to forest-green theme |
| **Icons Library** | Lucide React | `^0.475.0` | `frontend/src/components/` | Consistent, accessible iconography |
| **File Dropzone** | React Dropzone | `^14.3.5` | `frontend/src/pages/AnalyzeFood.tsx` | Drag-and-drop food image acquisition |
| **HTTP Client (Client)** | Axios | `^1.7.9` | `frontend/src/services/api.ts` | Promise-based HTTP client with global error interceptors |
| **Routing** | React Router DOM | `^7.1.5` | `frontend/src/App.tsx` | Client-side routing and layout orchestration |
| **Backend Framework** | FastAPI | `0.115.0+` | `backend/app/main.py` | Asynchronous high-throughput ASGI REST API server |
| **ASGI Web Server** | Uvicorn | `0.30.0+` | `backend/run.py` / CLI | High-performance ASGI production server |
| **Data Validation** | Pydantic v2 | `2.9.0+` | `backend/app/schemas/` | Robust request/response validation and serialization |
| **Configuration** | Pydantic Settings | `2.5.0+` | `backend/app/core/config.py` | Typed environment variable loading from `.env` |
| **Language (Backend)** | Python | `3.12.8` | `backend/` | Backend application, machine learning, and RAG execution |
| **Deep Learning Engine** | PyTorch | `2.5.0+` | `backend/app/services/classifier.py` | Neural network model loading and forward-pass inference |
| **Computer Vision Tool** | Torchvision | `0.20.0+` | `backend/app/services/classifier.py` | Image transforms and MobileNetV3 architecture definition |
| **Vision Model** | MobileNetV3-Large | Checkpoint | `backend/models/nutriguide_classifier.pth` | 20-class food image classification (17.1 MB) |
| **Image Processing** | Pillow (PIL) | `10.4.0+` | `backend/app/services/classifier.py` | Image ingestion, RGB conversion, and byte decoding |
| **Generative AI & Vision** | Google Gemma 3 4B IT (Ollama) | `gemma3:4b` | `backend/app/services/ollama_service.py` | Local multimodal vision fallback & nutrition reasoning |
| **Embedding Model** | Sentence Transformers | `all-MiniLM-L6-v2` | `backend/app/rag/rag_service.py` | 384-dimensional dense semantic text embeddings |
| **Vector Index** | FAISS CPU | `faiss-cpu 1.8.0+` | `backend/app/rag/rag_service.py` | High-speed Euclidean $L_2$ vector similarity search |
| **Async HTTP Client** | HTTPX | `0.27.0+` | `backend/app/services/` | Asynchronous requests to USDA and Open Food Facts APIs |
| **Test Framework** | Pytest | `9.1.1` | `backend/tests/` | Automated unit and integration testing suite |
| **Async Test Plugin** | Pytest Asyncio | `1.4.0` | `backend/tests/` | Native asynchronous fixture and test case execution |

---

## 2. Deep-Dive Technology Analysis

### 2.1 Presentation Tier

#### React 19 & TypeScript
- **Where Used:** Entire frontend UI (`frontend/src/`).
- **Why Selected:** React 19 introduces optimized concurrent rendering, improved action hooks, and reduced re-render overhead. TypeScript guarantees type safety between client components and backend Pydantic schemas, eliminating runtime `undefined` attribute exceptions.
- **Advantages:** Component modularity, rich ecosystem, type contracts matching backend schemas.
- **Limitations:** Client-side rendering requires initial JavaScript bundle execution; addressed by code splitting and Vite compression (total bundle gzip size: 121 kB).

#### Tailwind CSS v4
- **Where Used:** Global styling across all components and pages.
- **Why Selected:** The CSS-first engine of Tailwind v4 offers zero-runtime style generation, unified design token declarations, and instant compilation.
- **Advantages:** Eliminates CSS naming collisions; enforces brand color consistency (`#0d2818` forest green, `#2d6a4f` deep green, `#52b788` emerald accent).
- **Limitations:** Long utility class chains in JSX markup; mitigated by extracting reusable styled subcomponents (`NutritionCard`, `ConfidenceBadge`).

---

### 2.2 Application Server Tier

#### FastAPI & Uvicorn
- **Where Used:** Backend server core (`backend/app/main.py`).
- **Why Selected:** FastAPI provides automatic OpenAPI/Swagger documentation generation, native asynchronous Python execution (`async/await`), and seamless integration with Pydantic v2.
- **Advantages:** Benchmarked as one of the fastest Python web frameworks, matching Go and NodeJS speeds. Native async handling allows concurrent upstream queries to USDA, Open Food Facts, and Gemini without blocking worker threads.
- **Limitations:** Requires strict typing discipline; synchronous operations within async route handlers can block the event loop if not isolated (resolved via `asyncio.to_thread`).

---

### 2.3 Computer Vision & Machine Learning

#### PyTorch & MobileNetV3-Large
- **Where Used:** Food classification engine (`backend/app/services/classifier.py`).
- **Why Selected:** Designed specifically for edge and mobile environments, MobileNetV3-Large utilizes depthwise separable convolutions, inverted residual bottlenecks, and hardware-friendly squeeze-and-excitation layers.
- **Advantages:** Lightweight footprint (17.1 MB checkpoint), low parameter count (~4.2M parameters), and rapid inference latency (**24.83 ms** average on CPU).
- **Limitations:** Standard ImageNet weights lack specific food dish representations; resolved by fine-tuning on 15,000 Food-101 images, boosting accuracy from 2.60% to 90.64% Top-1.

---

### 2.4 External Data & Intelligence APIs

#### USDA FoodData Central API
- **Where Used:** Nutrition retrieval engine (`backend/app/services/nutrition.py`).
- **Why Selected:** USDA FoodData Central is the gold standard authoritative scientific food database maintained by the U.S. Department of Agriculture.
- **Advantages:** Highly accurate, peer-reviewed macro- and micronutrient quantities per 100g.
- **Limitations:** Strict hourly rate limits on default `DEMO_KEY` and complex nutrient ID hierarchies; resolved by supporting user-configured personal keys (`USDA_API_KEY`) and implementing an offline Standard Reference fallback.

#### Open Food Facts API
- **Where Used:** Packaged products and allergen engine (`backend/app/services/openfoodfacts.py`).
- **Why Selected:** Open Food Facts is the world's largest open, crowd-sourced database of commercial food products, encompassing over 3 million items globally.
- **Advantages:** Worldwide barcode coverage (EAN-13, UPC-A), ingredient formulations, and declared allergen metadata.
- **Limitations:** Occasional server timeouts or community-uploaded field omissions; resolved by multi-host failover (`world.openfoodfacts.net` / `world.openfoodfacts.org`) and safety disclaimers for unlisted allergens.

#### Google Gemma 3 4B IT (via Ollama)
- **Where Used:** Multimodal vision fallback, conversational AI assistant, and food comparison summaries (`backend/app/services/ollama_service.py`).
- **Why Selected:** Gemma 3 4B IT is Google's state-of-the-art compact multimodal instruction-tuned model. Running locally through Ollama provides 100% data privacy, zero API quota limitations, and zero cost, while running efficiently on consumer hardware (such as an NVIDIA RTX 3050 4 GB GPU + 16 GB RAM).
- **Advantages:** Multimodal capability (processes both image inputs and structured text queries); zero cloud latency / egress; immune to remote API rate limits; strict adherence to injected USDA/OFF ground truth evidence.
- **Limitations:** Initial inference requires loading weights into VRAM/RAM; resolved by Ollama's model preloading, connection timeouts with fast connection rejection (`connect=5.0s`), and fallback error messages advising users if Ollama is not active.

---

### 2.5 Retrieval-Augmented Generation (RAG)

#### Sentence Transformers (`all-MiniLM-L6-v2`) & FAISS
- **Where Used:** Semantic knowledge retrieval (`backend/app/rag/rag_service.py`).
- **Why Selected:** `all-MiniLM-L6-v2` produces compact 384-dimensional dense semantic vectors with fast CPU encoding. FAISS provides lightning-fast nearest-neighbor search with negligible memory overhead.
- **Advantages:** Enables zero-latency semantic search over domain nutrition documents without requiring expensive external vector database subscriptions (e.g., Pinecone).
- **Limitations:** Flat $L_2$ index does not scale to billions of vectors; for NutriGuide's curated domain set (20-100 documents), exact flat indexing provides 100% recall with zero quantization error.
