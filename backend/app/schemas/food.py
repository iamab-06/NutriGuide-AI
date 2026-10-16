"""
NutriGuide AI - Pydantic Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class NutrientInfo(BaseModel):
    name: str
    amount: float
    unit: str
    daily_value_pct: Optional[float] = None


class NutritionData(BaseModel):
    food_name: str
    source: str = "USDA FoodData Central"
    fdcId: Optional[int] = None
    serving_size: Optional[float] = None
    serving_size_unit: Optional[str] = "g"
    basis: str = "per 100g"
    calories: Optional[float] = None
    protein: Optional[float] = None
    carbohydrates: Optional[float] = None
    fat: Optional[float] = None
    sugar: Optional[float] = None
    fiber: Optional[float] = None
    sodium: Optional[float] = None
    cholesterol: Optional[float] = None
    saturated_fat: Optional[float] = None
    nutrients: List[NutrientInfo] = Field(default_factory=list)
    data_available: bool = True
    notes: Optional[str] = None


class ClassificationResult(BaseModel):
    predicted_class: str
    display_name: str
    confidence: float
    top_predictions: List[Dict[str, Any]] = Field(default_factory=list)
    is_confident: bool
    confidence_threshold: float = 0.4
    model_version: str = "MobileNetV3-NutriGuide-v1"
    supported_categories: List[str] = Field(default_factory=list)


class AnalyzeImageResponse(BaseModel):
    classification: ClassificationResult
    nutrition: Optional[NutritionData] = None
    message: str = ""
    error: Optional[str] = None


class ProductInfo(BaseModel):
    product_name: Optional[str] = None
    brands: Optional[str] = None
    ingredients_text: Optional[str] = None
    allergens: Optional[str] = None
    allergens_tags: List[str] = Field(default_factory=list)
    nutriments: Optional[Dict[str, Any]] = None
    image_url: Optional[str] = None
    barcode: Optional[str] = None
    source: str = "Open Food Facts"
    data_complete: bool = False
    missing_fields: List[str] = Field(default_factory=list)


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    food_context: Optional[Dict[str, Any]] = None
    history: List[ChatMessage] = Field(default_factory=list)


class ChatResponse(BaseModel):
    answer: str
    sources: List[str] = Field(default_factory=list)
    evidence_used: bool = False
    warning: Optional[str] = None


class FoodSearchResult(BaseModel):
    fdcId: int
    description: str
    food_category: Optional[str] = None
    brand_owner: Optional[str] = None
    score: Optional[float] = None


class CompareRequest(BaseModel):
    food1: str
    food2: str


class CompareResponse(BaseModel):
    food1: NutritionData
    food2: NutritionData
    basis: str = "per 100g"
    comparison_notes: Optional[str] = None
    ai_summary: Optional[str] = None
