# NutriGuide AI

An AI-powered food nutrition analysis web application built for the Department of Computer Science and Engineering, Siddaganga Institute of Technology (Academic Project 2026).

## Features

| Feature | Technology |
|---|---|
| Food Image Classification | MobileNetV3-Large (PyTorch) |
| Nutrition Data | USDA FoodData Central API |
| Allergen & Ingredient Info | Open Food Facts API |
| AI Explanations | Google Gemini 1.5 Flash |
| Semantic Retrieval (RAG) | Sentence Transformers + FAISS |
| Frontend | React + Vite + TypeScript + Tailwind CSS |
| Backend | FastAPI + Python 3.12 |

## Supported Food Categories (20)

Apple Pie, Caesar Salad, Chicken Curry, Chocolate Cake, Donuts, French Fries, Fried Rice, Hamburger, Hot Dog, Ice Cream, Omelette, Pancakes, Pizza, Ramen, Samosa, Spaghetti Bolognese, Spring Rolls, Steak, Sushi, Waffles

## Setup

### 1. Clone and configure environment

```bash
cp .env.example .env
# Edit .env and add your API keys:
# - GEMINI_API_KEY (required for AI features)
# - USDA_API_KEY (get free key at https://fdc.nal.usda.gov/api-guide.html)
```

### 2. Backend setup

```bash
cd backend
pip install -r requirements.txt
# Start the backend:
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 in your browser.

## API Keys Required

| Key | Where to Get | Required |
|---|---|---|
| `GEMINI_API_KEY` | [Google AI Studio](https://aistudio.google.com/app/apikey) | Yes (for AI features) |
| `USDA_API_KEY` | [FoodData Central](https://fdc.nal.usda.gov/api-guide.html) | Yes (for nutrition data) |
| Open Food Facts | No key needed | N/A |

> **Note:** Without `GEMINI_API_KEY`, the AI assistant and comparison summary will not work. Without `USDA_API_KEY`, use `DEMO_KEY` (rate limited to 30 req/hr).

## Architecture

```
nutriguide-ai/
├── frontend/          # React + Vite + TypeScript
│   └── src/
│       ├── pages/     # Dashboard, AnalyzeFood, NutritionInfo, etc.
│       ├── components/# NutritionCard, Layout, etc.
│       ├── services/  # API client (axios)
│       └── types/     # TypeScript interfaces
├── backend/           # FastAPI + Python
│   └── app/
│       ├── api/       # Route handlers
│       ├── services/  # Classifier, USDA, Open Food Facts, Gemini
│       ├── rag/       # FAISS + Sentence Transformers
│       ├── schemas/   # Pydantic models
│       └── core/      # Config, categories
├── models/            # Fine-tuned model weights (not in git)
└── datasets/          # Training data (not in git)
```

## ML Model Details

- **Architecture:** MobileNetV3-Large with custom 20-class head
- **Training data:** Food-101 subset (20 categories)
- **Confidence threshold:** 40% (below this, user is asked to confirm)
- **Fallback:** Uses ImageNet pretrained backbone if no fine-tuned weights found

## Data Sources

- **USDA FoodData Central:** Primary source for nutritional values (per 100g)
- **Open Food Facts:** Packaged product ingredients and allergens (community database)
- **NutriGuide Knowledge Base:** 20 curated nutrition reference documents for RAG

## Safety & Limitations

- The classifier recognizes only 20 food categories from Food-101
- Nutritional values come from USDA and are retrieved per 100g
- Allergen absence in Open Food Facts does NOT confirm allergen-free status
- The AI assistant never invents nutritional values — it uses only retrieved data
- This application does not provide medical or dietary advice

## Evaluation Criteria

See `docs/evaluation.md` for the complete evaluation checklist and test results.

## Academic Context

**Course:** Department of Computer Science and Engineering  
**Institution:** Siddaganga Institute of Technology  
**Deadline:** October 30, 2026  
**Project Type:** AI/ML Capstone — Multimodal Generative AI Application
