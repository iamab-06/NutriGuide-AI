# NutriGuide AI — Setup & Execution Guide

**Project:** NutriGuide AI  
**Institution:** Department of Computer Science and Engineering, Siddaganga Institute of Technology  
**Academic Year:** 2026  

---

## 1. Prerequisites & System Requirements

### 1.1 Software Dependencies
- **Operating System:** Windows 10/11, macOS (12+), or Ubuntu Linux (20.04+)
- **Python:** Version `3.10`, `3.11`, or `3.12` (Python 3.12.8 verified)
- **Node.js:** Version `18.x`, `20.x`, or `22.x` (with `npm 10+`)
- **Git:** Version `2.30+`
- **Ollama:** Version `0.1.30+` (for running local Gemma 3 4B IT multimodal LLM)

### 1.2 Hardware Recommendations
- **Processor:** Modern multi-core CPU (Intel Core i5/i7 or AMD Ryzen 5/7, e.g., AMD Ryzen 7 5800H)
- **RAM:** Minimum 8 GB (16 GB recommended for running local Gemma 3 4B IT alongside backend and frontend)
- **GPU (Recommended):** NVIDIA GPU with 4 GB+ VRAM (e.g., NVIDIA GeForce RTX 3050 4 GB Laptop GPU) for GPU acceleration; falls back cleanly to CPU with quantized weights.
- **Disk Space:** ~8 GB free disk space (includes ~3.3 GB for Gemma 3 4B IT model, PyTorch weights, and datasets)

---

## 2. Step-by-Step Installation

### Step 2.1: Clone & Navigate to Repository
```bash
git clone https://github.com/nutriguide-ai/nutriguide-ai.git
cd nutriguide-ai
```

### Step 2.2: Backend Python Environment Setup
1. Open terminal and navigate to `backend/`:
   ```bash
   cd backend
   ```
2. Create and activate a Python virtual environment:
   - **Windows (PowerShell):**
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```
   - **Linux / macOS:**
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```
3. Install backend dependencies:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

### Step 2.3: Backend Environment Configuration (`.env`)
1. Create a `.env` file in the `backend/` directory from the template:
   - **Windows:**
     ```powershell
     Copy-Item .env.example .env
     ```
   - **Linux / macOS:**
     ```bash
     cp .env.example .env
     ```
2. Open `backend/.env` in your editor and configure:
   ```env
   # Ollama / Gemma 3 4B IT (Local Multimodal LLM - No API Key Required)
   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_MODEL=gemma3:4b
   OLLAMA_TIMEOUT=120

   # USDA FoodData Central API Key (Recommended for live nutrition queries)
   USDA_API_KEY=your_actual_usda_api_key_here

   # Application Configuration
   BACKEND_HOST=0.0.0.0
   BACKEND_PORT=8000
   CONFIDENCE_THRESHOLD=0.70
   ```
   *(Note: If `USDA_API_KEY` is not provided, the system defaults to `DEMO_KEY` and local reference fallbacks).*

### Step 2.4: Local LLM Setup (Ollama & Gemma 3 4B IT)
NutriGuide AI runs Google Gemma 3 4B IT locally via Ollama. This provides complete data privacy, zero API quota limitations, and zero cost.

1. **Download & Install Ollama:**
   - **Windows:** Download the installer from [https://ollama.com/download/windows](https://ollama.com/download/windows) and run the installer.
   - **macOS / Linux:** Follow instructions on [https://ollama.com](https://ollama.com).

2. **Start the Ollama Server:**
   ```bash
   ollama serve
   ```
   Ollama runs at `http://localhost:11434` by default.

3. **Pull the Gemma 3 4B IT Model:**
   In a terminal, run:
   ```bash
   ollama pull gemma3:4b
   ```
   *Download size: ~3.3 GB. Gemma 3 4B IT is a multimodal model capable of both text comprehension and vision analysis.*

4. **Verify Installation:**
   ```bash
   ollama list
   ```
   Confirm that `gemma3:4b` is listed.

### Step 2.5: Frontend Node Environment Setup
1. In a separate terminal, navigate to `frontend/`:
   ```bash
   cd frontend
   ```
2. Install frontend dependencies:
   ```bash
   npm install
   ```

---

## 3. Running the Application

### 3.1 Start the Local Ollama Server
Ensure the Ollama background daemon is active:
```bash
ollama serve
```
*(On Windows, Ollama usually starts automatically upon installation in the system tray).*

### 3.2 Start the Backend Server
From the `backend/` directory with virtual environment activated:
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
- **Backend API:** `http://127.0.0.1:8000`
- **Interactive Swagger Documentation:** `http://127.0.0.1:8000/docs`
- **ReDoc Documentation:** `http://127.0.0.1:8000/redoc`

### 3.3 Start the Frontend Development Server
From the `frontend/` directory:
```bash
npm run dev
```
- **Frontend Web UI:** `http://localhost:5173`
- The Vite development server automatically proxies all `/api/*` network requests to `http://127.0.0.1:8000/api/*`.

---

## 4. Verification & Testing

### 4.1 Run Backend Automated Tests
From the `backend/` directory:
```powershell
python -m pytest -v
```
*Expected: 37 tests passed in ~70s.*

### 4.2 Run Latency & Accuracy Benchmark
From the `backend/` directory:
```powershell
$env:PYTHONPATH="."
python tests/benchmark.py
```
*Expected: Average classification latency ~24.83 ms, 100% entity coverage.*

### 4.3 Run End-to-End User Journey Tests
Ensure both backend (`:8000`) and frontend (`:5173`) are running, then execute:
```powershell
$env:PYTHONPATH="."
python tests/verify_journeys.py
```
*Expected: All 5 user journeys passed.*

### 4.4 Run Frontend Production Build
From the `frontend/` directory:
```bash
npm run build
```
*Expected: Built in ~1.2s with zero errors.*
