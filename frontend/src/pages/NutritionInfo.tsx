import { useState } from 'react'
import { Search, Loader2 } from 'lucide-react'
import { searchNutrition, getNutrition } from '../services/api'
import type { NutritionData, FoodSearchResult } from '../types'
import NutritionCard from '../components/NutritionCard'
import ErrorMessage from '../components/ErrorMessage'

export default function NutritionInfo() {
  const [query, setQuery] = useState('')
  const [searchResults, setSearchResults] = useState<FoodSearchResult[]>([])
  const [nutrition, setNutrition] = useState<NutritionData | null>(null)
  const [loading, setLoading] = useState(false)
  const [detailLoading, setDetailLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [searched, setSearched] = useState(false)

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return
    setLoading(true)
    setError(null)
    setNutrition(null)
    setSearchResults([])
    setSearched(true)
    try {
      const results = await searchNutrition(query.trim())
      setSearchResults(results)
      if (results.length === 0) {
        setError(`No results found for "${query}". Try a different search term.`)
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Search failed.')
    } finally {
      setLoading(false)
    }
  }

  const handleSelectFood = async (food: FoodSearchResult) => {
    setDetailLoading(true)
    setError(null)
    setNutrition(null)
    try {
      const data = await getNutrition(food.description)
      setNutrition(data)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load nutrition data.')
    } finally {
      setDetailLoading(false)
    }
  }

  return (
    <div className="p-6 lg:p-8 max-w-4xl mx-auto">
      {/* Search */}
      <form onSubmit={handleSearch} className="flex gap-3 mb-6">
        <div className="flex-1 relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search for a food (e.g., pizza, chicken, apple)"
            className="w-full pl-12 pr-4 py-3 rounded-xl border border-gray-200 bg-white text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-[#52b788] focus:border-transparent transition-all"
          />
        </div>
        <button
          type="submit"
          disabled={loading || !query.trim()}
          className="px-6 py-3 bg-[#2d6a4f] hover:bg-[#1a3d2b] disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold rounded-xl transition-all flex items-center gap-2"
        >
          {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Search className="w-5 h-5" />}
          Search
        </button>
      </form>

      {error && <ErrorMessage message={error} />}

      {/* Search results */}
      {searchResults.length > 0 && !nutrition && (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden mb-6">
          <div className="px-6 py-4 border-b border-gray-50">
            <p className="font-semibold text-gray-700">{searchResults.length} results — select one to view nutrition details</p>
          </div>
          <div className="divide-y divide-gray-50">
            {searchResults.map((food) => (
              <button
                key={food.fdcId}
                onClick={() => handleSelectFood(food)}
                disabled={detailLoading}
                className="w-full flex items-start justify-between px-6 py-4 hover:bg-[#f8fdf9] transition-colors text-left"
              >
                <div>
                  <p className="font-medium text-gray-900">{food.description}</p>
                  {food.food_category && <p className="text-sm text-gray-500">{food.food_category}</p>}
                  {food.brand_owner && <p className="text-xs text-gray-400">{food.brand_owner}</p>}
                </div>
                <span className="text-xs text-[#2d6a4f] bg-[#e8f4ed] px-2 py-1 rounded-lg mt-1 flex-shrink-0">FDC #{food.fdcId}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {detailLoading && (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-8">
          <div className="flex items-center gap-3 justify-center">
            <Loader2 className="w-6 h-6 text-[#2d6a4f] animate-spin" />
            <span className="text-gray-600">Retrieving nutrition data...</span>
          </div>
        </div>
      )}

      {nutrition && (
        <div className="space-y-4">
          <NutritionCard data={nutrition} />
          <button
            onClick={() => { setNutrition(null) }}
            className="text-sm text-[#2d6a4f] hover:text-[#1a3d2b] font-medium transition-colors"
          >
            ← Back to search results
          </button>
        </div>
      )}

      {!searched && (
        <div className="bg-[#e8f4ed] rounded-2xl p-8 text-center">
          <Search className="w-12 h-12 text-[#2d6a4f] mx-auto mb-4" />
          <p className="text-[#2d6a4f] font-semibold">Search for any food</p>
          <p className="text-sm text-[#40916c] mt-2">Try: pizza, chicken curry, apple, brown rice...</p>
        </div>
      )}
    </div>
  )
}
