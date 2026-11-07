export interface NutrientInfo {
  name: string
  amount: number
  unit: string
  daily_value_pct?: number | null
}

export interface NutritionData {
  food_name: string
  source: string
  fdcId?: number | null
  serving_size?: number | null
  serving_size_unit?: string
  basis: string
  calories?: number | null
  protein?: number | null
  carbohydrates?: number | null
  fat?: number | null
  sugar?: number | null
  fiber?: number | null
  sodium?: number | null
  cholesterol?: number | null
  saturated_fat?: number | null
  nutrients: NutrientInfo[]
  data_available: boolean
  notes?: string | null
}

export interface TopPrediction {
  class: string
  display_name: string
  confidence: number
  confidence_pct: string
}

export interface ClassificationResult {
  predicted_class: string
  display_name: string
  confidence: number
  top_predictions: TopPrediction[]
  is_confident: boolean
  confidence_threshold: number
  model_version: string
  supported_categories: string[]
}

export interface GeminiVisionFallback {
  available: boolean
  is_food?: boolean
  suggested_food?: string | null
  category_match?: string | null
  confidence?: string | null
  explanation?: string | null
  source: string
  error?: string | null
}

export interface ConditionItem {
  id: string
  name: string
  category: string
  icon: string
  description: string
}

export interface ConditionEvaluation {
  condition_id: string
  condition_name: string
  status: 'SAFE' | 'MODERATE' | 'RESTRICTED'
  headline: string
  explanation: string
  recommendation?: string | null
}

export interface HealthSafetyReport {
  overall_status: 'SAFE' | 'MODERATE' | 'RESTRICTED'
  summary: string
  evaluations: ConditionEvaluation[]
  disclaimer: string
}

export interface MealComponent {
  name: string
  category_key?: string | null
  portion_g: number
  serving_description: string
  calories: number
  protein: number
  carbohydrates: number
  fat: number
  fiber?: number | null
  sugar?: number | null
  sodium?: number | null
  source: string
  notes?: string | null
}

export interface MealPlateAnalysis {
  is_plate: boolean
  meal_title: string
  items_detected_count: number
  components: MealComponent[]
  total_calories: number
  total_protein: number
  total_carbohydrates: number
  total_fat: number
  total_fiber: number
  total_sugar: number
  total_sodium: number
  macro_ratios: {
    carbohydrates_pct: number
    protein_pct: number
    fat_pct: number
  }
  health_safety?: HealthSafetyReport | null
  visual_summary?: string | null
  source: string
}

export interface AnalyzeImageResponse {
  classification: ClassificationResult
  nutrition?: NutritionData | null
  message: string
  error?: string | null
  gemini_fallback?: GeminiVisionFallback | null
  requires_confirmation?: boolean
  is_food?: boolean
  health_safety?: HealthSafetyReport | null
  plate_analysis?: MealPlateAnalysis | null
}

export interface ProductInfo {
  product_name?: string | null
  brands?: string | null
  ingredients_text?: string | null
  allergens?: string | null
  allergens_tags: string[]
  nutriments?: Record<string, unknown> | null
  image_url?: string | null
  barcode?: string | null
  source: string
  data_complete: boolean
  missing_fields: string[]
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface ChatResponse {
  answer: string
  sources: string[]
  evidence_used: boolean
  warning?: string | null
}

export interface FoodSearchResult {
  fdcId: number
  description: string
  food_category?: string | null
  brand_owner?: string | null
  score?: number | null
}

export interface CompareResponse {
  food1: NutritionData
  food2: NutritionData
  basis: string
  comparison_notes?: string | null
  ai_summary?: string | null
}
