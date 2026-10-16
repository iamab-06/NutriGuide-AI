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

export interface AnalyzeImageResponse {
  classification: ClassificationResult
  nutrition?: NutritionData | null
  message: string
  error?: string | null
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
