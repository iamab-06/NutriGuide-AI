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
    source_id: Optional[str] = None
    verification_status: Optional[str] = "verified_standard"
    atwater_discrepancy_pct: Optional[float] = None
    is_validated: bool = True


class ClassificationResult(BaseModel):
    predicted_class: str
    display_name: str
    confidence: float
    top_predictions: List[Dict[str, Any]] = Field(default_factory=list)
    is_confident: bool
    confidence_threshold: float = 0.70
    model_version: str = "MobileNetV3-NutriGuide-v1"
    supported_categories: List[str] = Field(default_factory=list)


class GeminiVisionFallback(BaseModel):
    available: bool = False
    is_food: bool = True
    suggested_food: Optional[str] = None
    category_match: Optional[str] = None
    confidence: Optional[str] = None
    explanation: Optional[str] = None
    source: str = "Google Gemini Vision"
    error: Optional[str] = None


class AnalyzeImageResponse(BaseModel):
    classification: ClassificationResult
    nutrition: Optional[NutritionData] = None
    message: str = ""
    error: Optional[str] = None
    gemini_fallback: Optional[GeminiVisionFallback] = None
    requires_confirmation: bool = False
    is_food: bool = True
    health_safety: Optional['HealthSafetyReport'] = None
    plate_analysis: Optional['MealPlateAnalysis'] = None


class ConditionEvaluation(BaseModel):
    condition_id: str
    condition_name: str
    status: str  # "SAFE", "MODERATE", "RESTRICTED"
    headline: str
    explanation: str
    recommendation: Optional[str] = None


class HealthSafetyReport(BaseModel):
    overall_status: str  # "SAFE", "MODERATE", "RESTRICTED"
    summary: str
    evaluations: List[ConditionEvaluation] = Field(default_factory=list)
    disclaimer: str = (
        "Educational nutritional screening based on ICMR-NIN & WHO dietary references. "
        "Not clinical medical advice."
    )


class EvaluateConditionsRequest(BaseModel):
    food_name: str
    nutrition: Optional[NutritionData] = None
    conditions: List[str] = Field(default_factory=list)
    portion_g: float = 100.0


class MealComponent(BaseModel):
    name: str
    category_key: Optional[str] = None
    portion_g: float = 100.0
    serving_description: str = "1 serving"
    calories: float = 0.0
    protein: float = 0.0
    carbohydrates: float = 0.0
    fat: float = 0.0
    fiber: Optional[float] = 0.0
    sugar: Optional[float] = 0.0
    sodium: Optional[float] = 0.0
    source: str = "NutriGuide Knowledge Base"
    notes: Optional[str] = None


class MealPlateAnalysis(BaseModel):
    is_plate: bool = True
    meal_title: str = "Complete Meal Plate"
    items_detected_count: int = 0
    components: List[MealComponent] = Field(default_factory=list)
    total_calories: float = 0.0
    total_protein: float = 0.0
    total_carbohydrates: float = 0.0
    total_fat: float = 0.0
    total_fiber: float = 0.0
    total_sugar: float = 0.0
    total_sodium: float = 0.0
    macro_ratios: Dict[str, float] = Field(default_factory=dict)
    health_safety: Optional[HealthSafetyReport] = None
    visual_summary: Optional[str] = None
    source: str = "Gemma 3 Multimodal Vision + ICMR-NIN/USDA Database"


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
    role: str = Field(..., pattern=r"^(user|assistant|system)$")
    content: str = Field(default="", max_length=2000)


class ChatRequest(BaseModel):
    message: str = Field(default="", max_length=2000)
    food_context: Optional[Dict[str, Any]] = None
    history: List[ChatMessage] = Field(default_factory=list, max_length=20)


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
    food1: str = Field(default="", max_length=100)
    food2: str = Field(default="", max_length=100)


class CompareResponse(BaseModel):
    food1: NutritionData
    food2: NutritionData
    basis: str = "per 100g"
    comparison_notes: Optional[str] = None
    ai_summary: Optional[str] = None
