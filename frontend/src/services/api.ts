import axios from 'axios'
import type {
  AnalyzeImageResponse,
  NutritionData,
  ProductInfo,
  ChatResponse,
  FoodSearchResult,
  CompareResponse,
  ChatMessage,
  ConditionItem,
  HealthSafetyReport,
  MealPlateAnalysis,
} from '../types'

const API = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL !== undefined && import.meta.env.VITE_API_BASE_URL !== ''
    ? import.meta.env.VITE_API_BASE_URL
    : '',
  timeout: 90000,
})

// Interceptor for error normalization
API.interceptors.response.use(
  (res) => res,
  (err) => {
    let message = 'An unknown error occurred'
    if (err.response?.data?.detail) {
      message = typeof err.response.data.detail === 'string'
        ? err.response.data.detail
        : JSON.stringify(err.response.data.detail)
    } else if (err.response?.data?.message) {
      message = err.response.data.message
    } else if (err.code === 'ECONNABORTED' || err.message?.includes('timeout')) {
      message = 'Request timed out. Please try again.'
    } else if (err.message === 'Network Error' || !err.response) {
      message = 'Unable to connect to the backend server. Please verify the backend is running at http://127.0.0.1:8000.'
    } else if (err.message) {
      message = err.message
    }
    return Promise.reject(new Error(message))
  }
)

export const analyzeImage = async (
  file: File,
  conditions?: string[]
): Promise<AnalyzeImageResponse> => {
  const form = new FormData()
  form.append('file', file)
  if (conditions && conditions.length > 0) {
    form.append('conditions', conditions.join(','))
  }
  const { data } = await API.post<AnalyzeImageResponse>('/api/analyze', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export const analyzeMealPlate = async (
  file: File,
  conditions?: string[]
): Promise<MealPlateAnalysis> => {
  const form = new FormData()
  form.append('file', file)
  if (conditions && conditions.length > 0) {
    form.append('conditions', conditions.join(','))
  }
  const { data } = await API.post<MealPlateAnalysis>('/api/analyze-plate', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export const getHealthConditions = async (): Promise<ConditionItem[]> => {
  const { data } = await API.get<ConditionItem[]>('/api/health-advisor/conditions')
  return data
}

export const evaluateHealthSafety = async (
  foodName: string,
  categoryKey?: string,
  nutrition?: NutritionData | null,
  conditions: string[] = [],
  portionG = 100.0
): Promise<HealthSafetyReport> => {
  const { data } = await API.post<HealthSafetyReport>('/api/health-advisor/evaluate', {
    food_name: foodName,
    category_key: categoryKey || null,
    nutrition: nutrition || null,
    conditions,
    portion_g: portionG,
  })
  return data
}

export const getCategories = async (): Promise<Record<string, unknown>> => {
  const { data } = await API.get('/api/categories')
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

export interface StreamChatCallbacks {
  onToken: (token: string) => void
  onMeta?: (meta: { sources: string[]; evidence_used: boolean }) => void
  onError?: (error: string) => void
  onDone?: () => void
}

export const streamChat = async (
  message: string,
  foodContext?: Record<string, unknown>,
  history?: ChatMessage[],
  callbacks?: StreamChatCallbacks,
  signal?: AbortSignal
): Promise<void> => {
  const baseURL = import.meta.env.VITE_API_BASE_URL !== undefined && import.meta.env.VITE_API_BASE_URL !== ''
    ? import.meta.env.VITE_API_BASE_URL
    : ''
  const response = await fetch(`${baseURL}/api/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      food_context: foodContext || null,
      history: history || [],
    }),
    signal,
  })

  if (!response.ok) {
    throw new Error(`Server returned HTTP ${response.status}`)
  }

  const reader = response.body?.getReader()
  if (!reader) throw new Error('Response body stream is unavailable')

  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''

    for (const line of lines) {
      const trimmed = line.trim()
      if (trimmed.startsWith('data: ')) {
        const jsonStr = trimmed.slice(6)
        try {
          const parsed = JSON.parse(jsonStr)
          if (parsed.event === 'token' && parsed.token) {
            callbacks?.onToken(parsed.token)
          } else if (parsed.event === 'meta') {
            callbacks?.onMeta?.({
              sources: parsed.sources || [],
              evidence_used: parsed.evidence_used || false,
            })
          } else if (parsed.event === 'error') {
            callbacks?.onError?.(parsed.error || 'Streaming error')
          } else if (parsed.event === 'done') {
            callbacks?.onDone?.()
          }
        } catch {
          // ignore unparseable chunk
        }
      }
    }
  }
  callbacks?.onDone?.()
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
