# NutriGuide AI

An AI-powered multimodal food recognition, nutrition analysis, and ingredient awareness assistant built for the Department of Computer Science and Engineering, Siddaganga Institute of Technology (Academic Capstone Project 2026).

---

## 🌟 Key Features

| Feature | Technical Implementation |
|---|---|
| **Edge Food Classification** | PyTorch MobileNetV3-Large fine-tuned on Food-101 (20 classes, 90.64% Top-1, ~26.9 ms latency) |
| **Open-Vocabulary Vision Fallback** | Calibrated 70% threshold; ambiguous or non-standard dishes trigger **Google Gemma 3 4B IT Vision** multimodal fallback via Ollama for general-purpose recognition |
| **Defensive Safety Protocol** | Strict nutrition withholding (`nutrition = null`) on unconfirmed dishes until explicit user confirmation |
| **Numerical Validation Layer** | Atwater 4-4-9 macro-energy balance verification (tolerance ±35%), physical bound validation, sugar/carb and sat-fat/fat constraints with source provenance tracking |
| **Curated Reference Database** | Embedded SQLite relational store containing 120+ lab-verified Indian staples (ICMR-NIN IFCT 2017) and international foundations |
| **High-Performance Async Caching** | Thread-safe TTL LRU cache with single-flight request coalescing (0.01ms cached lookup, >290x speedup) |
| **Real-Time Token Streaming** | Server-Sent Events (SSE) `/api/chat/stream` delivering progressive token streams from Gemma 3 4B IT to React 19 UI |
| **Standardized Nutrition Data** | Authoritative macro- and micronutrients from **USDA FoodData Central** normalized per 100g |
| **Packaged Goods & Allergens** | Full-text product search and EAN-13 barcode lookups via **Open Food Facts** with allergen absence alerts |
| **Evidence-Grounded RAG Assistant** | Conversational reasoning powered by **Google Gemma 3 4B IT (Ollama)** + **FAISS L2 Flat** + **Sentence Transformers** |
| **Comparative Nutrition Matrix** | Side-by-side per-100g dietary comparison with automated AI synthesis |
| **Modern User Interface** | Responsive, accessible **React 19 + TypeScript + Vite 8** Single Page App styled with **Tailwind CSS v4** |

---

## 🍕 Food Recognition & Coverage Domain

- **Trained Local Vision Backbone (20 Core Categories):** Apple Pie, Caesar Salad, Chicken Curry, Chocolate Cake, Donuts, French Fries, Fried Rice, Hamburger, Hot Dog, Ice Cream, Omelette, Pancakes, Pizza, Ramen, Samosa, Spaghetti Bolognese, Spring Rolls, Steak, Sushi, Waffles.
- **Full Food-101 Taxonomy:** Catalog mappings available for all 101 official Food-101 categories.
- **Open-Vocabulary Gemma 3 Vision Fallback:** Recognizes regional dishes (e.g. Masala Dosa, Biryani, Dal Makhani) and open-ended preparations beyond fixed classes.
- **Curated Relational Database (120+ Foods):** Verified Indian staples (Roti, Dal, Paneer, Idli, Dosa, Khichdi, Poha, Upma, Naan) from ICMR-NIN IFCT 2017 + global foundation foods from USDA.
- **USDA FoodData Central API:** On-demand access to over 300,000 global commercial and agricultural food records.

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- **Python:** 3.10, 3.11, or 3.12 (Python 3.12.8 verified)
- **Node.js:** 18.x, 20.x, or 22.x (with npm)
- **Ollama:** [https://ollama.com](https://ollama.com) (for local Gemma 3 4B IT multimodal model)
- **Git**

### 2. Configure Environment Variables
Copy `backend/.env.example` to `backend/.env` and configure:
```bash
cp backend/.env.example backend/.env
```
Example `backend/.env`:
```env
# Ollama / Gemma 3 4B IT (Local Multimodal LLM - No API Key Required)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:4b
OLLAMA_TIMEOUT=120

# USDA FoodData Central API Key (Optional, defaults to DEMO_KEY)
USDA_API_KEY=your_usda_api_key_here

# Application Settings
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
CONFIDENCE_THRESHOLD=0.70
```

### 3. Backend Setup & Startup
```bash
cd backend
python -m venv venv
# Windows: .\venv\Scripts\Activate.ps1 | Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
- API Endpoint: `http://127.0.0.1:8000`
- Interactive OpenAPI Docs: `http://127.0.0.1:8000/docs`

### 4. Frontend Setup & Startup
In a separate terminal window:
```bash
cd frontend
npm install
npm run dev
```
Open **`http://localhost:5173`** in your browser.

---

## 🧪 Automated Testing & Verification

Run the full automated backend test suite (73 tests across 11 modules):
```bash
cd backend
python -m pytest -v
```

Run empirical classification latency and coverage benchmarks:
```bash
cd backend
python tests/benchmark.py
```

Run end-to-end user journeys through the Vite proxy:
```bash
cd backend
python tests/verify_journeys.py
```

Run frontend production build:
```bash
cd frontend
npm run build
```

---

## 📚 Complete Project Documentation Package

The project contains an extensive, academic-grade documentation suite located in the [`docs/`](docs/) directory:

### Core Documentation
- 📄 [**Complete Project Report**](docs/PROJECT_REPORT.md): 39-section comprehensive academic project report.
- 📄 [**Project Abstract**](docs/ABSTRACT.md): Concise executive summary and keywords.
- 📄 [**Problem Statement & Objectives**](docs/PROBLEM_STATEMENT_AND_OBJECTIVES.md): Problem analysis, scope, and engineering objectives.
- 📄 [**System Architecture Specification**](docs/SYSTEM_ARCHITECTURE.md): Multi-tier architectural design and component specifications.
- 📄 [**Technology Stack Justification**](docs/TECHNOLOGY_STACK.md): Exhaustive analysis of all frontend, backend, ML, and API technologies.
- 📄 [**Implementation Details**](docs/IMPLEMENTATION_DETAILS.md): Code walkthrough, schemas, lifecycle management, and file-by-file analysis.
- 📄 [**Datasets & Data Sources**](docs/DATASETS_AND_DATA_SOURCES.md): Food-101 splits, USDA extraction, Open Food Facts, and knowledge bases.
- 📄 [**REST API Documentation**](docs/API_DOCUMENTATION.md): Complete endpoint catalog, request/response JSON schemas, and status codes.
- 📄 [**AI & RAG Pipeline Specification**](docs/AI_AND_RAG_PIPELINE.md): Vision pipeline, 70% threshold, Gemma 3 Vision fallback, and FAISS RAG.
- 📄 [**Testing & Evaluation Report**](docs/TESTING_AND_EVALUATION.md): Test methodology, latency benchmarks, and journey validations.
- 📄 [**Engineering Challenges & Solutions**](docs/DEVELOPMENT_CHALLENGES.md): Analysis of 15 major development bottlenecks and root-cause fixes.
- 📄 [**Limitations & Future Scope**](docs/LIMITATIONS_AND_FUTURE_SCOPE.md): Current boundaries, 3D portion sizing roadmap, and future research.
- 📄 [**Security & Configuration Guide**](docs/SECURITY_AND_CONFIGURATION.md): Credential isolation, input sanitization, and defensive design.
- 📄 [**Setup & Execution Guide**](docs/SETUP_AND_EXECUTION_GUIDE.md): Cross-platform installation and startup procedures.
- 📄 [**Technical Viva Q&A (55 Questions)**](docs/VIVA_QUESTIONS_AND_ANSWERS.md): Complete preparation guide for viva voce and defense.
- 📄 [**Presentation Outline (18 Slides)**](docs/PRESENTATION_OUTLINE.md): Master slide-by-slide presentation plan with notes.
- 📄 [**Classroom Demo Guide**](docs/PROJECT_DEMO_GUIDE.md): Scripted live demonstration walkthrough and test cases.
- 📄 [**Academic & Technical References**](docs/REFERENCES.md): Authoritative IEEE/APA bibliography and official documentation links.

### Architecture & Pipeline Diagrams
- 📊 [**System Architecture Diagram**](docs/diagrams/system_architecture.mmd)
- 📊 [**Food Recognition Pipeline Diagram**](docs/diagrams/food_recognition_pipeline.mmd)
- 📊 [**Gemini Vision Fallback Sequence Diagram**](docs/diagrams/gemini_vision_fallback.mmd)
- 📊 [**RAG Pipeline Diagram**](docs/diagrams/rag_pipeline.mmd)
- 📊 [**Data Flow Diagram**](docs/diagrams/data_flow.mmd)

### Empirical Evidence & Test Logs
- 📋 [**Automated Test Execution Log (37/37 Passed)**](docs/evidence/TEST_RESULTS.md)
- 📋 [**Empirical Model Evaluation & Benchmark Results**](docs/evidence/EVALUATION_RESULTS.md)

---

## 🏛️ Academic Context & Credits

- **Institution:** Siddaganga Institute of Technology, Tumakuru, Karnataka
- **Department:** Department of Computer Science and Engineering
- **Academic Degree:** Bachelor of Engineering in Computer Science and Engineering
- **Academic Target:** Final Capstone Submission (October 2026)
- **Supervision:** Department Faculty Guides, Department of CSE, SIT Tumakuru
