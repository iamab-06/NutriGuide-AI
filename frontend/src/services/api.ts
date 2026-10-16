import axios from 'axios'
import type {
  AnalyzeImageResponse,
  NutritionData,
  ProductInfo,
  ChatResponse,
  FoodSearchResult,
  CompareResponse,
  ChatMessage,
} from '../types'

const API = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 60000,
})

// Interceptor for error normalization
API.interceptors.response.use(
  (res) => res,
  (err) => {
    const message =
      err.response?.data?.detail ||
      err.response?.data?.message ||
      err.message ||
      'An unknown error occurred'
    return Promise.reject(new Error(message))
  }
)

export const analyzeImage = async (file: File): Promise<AnalyzeImageResponse> => {
  const form = new FormData()
  form.append('file', file)
  const { data } = await API.post<AnalyzeImageResponse>('/api/analyze', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export const searchNutrition = async (q: string): Promise<FoodSearchResult[]> => {
  const { data } = await API.get('/api/nutrition/search', { params: { q } })
  return data.results || []
}

export const getNutrition = async (
  foodName: string,
  categoryKey?: string
): Promise<NutritionData> => {
  const { data } = await API.get(`/api/nutrition/${encodeURIComponent(foodName)}`, {
    params: categoryKey ? { category_key: categoryKey } : {},
  })
  return data
}

export const searchProducts = async (q: string, pageSize = 5): Promise<ProductInfo[]> => {
  const { data } = await API.get('/api/products/search', { params: { q, page_size: pageSize } })
  return data.results || []
}

export const getProductByBarcode = async (barcode: string): Promise<ProductInfo> => {
  const { data } = await API.get(`/api/products/barcode/${barcode}`)
  return data
}

export const chat = async (
  message: string,
  foodContext?: Record<string, unknown>,
  history?: ChatMessage[]
): Promise<ChatResponse> => {
  const { data } = await API.post<ChatResponse>('/api/chat', {
    message,
    food_context: foodContext || null,
    history: history || [],
  })
  return data
}

export const compareFoods = async (
  food1: string,
  food2: string
): Promise<CompareResponse> => {
  const { data } = await API.post<CompareResponse>('/api/compare', { food1, food2 })
  return data
}

export const healthCheck = async () => {
  const { data } = await API.get('/api/health')
  return data
}
