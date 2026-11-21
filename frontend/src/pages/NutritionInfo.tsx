import { useState } from 'react'
import { Search, Loader2, ArrowLeft, ExternalLink, PieChart as PieIcon, Database, CheckCircle2 } from 'lucide-react'
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip } from 'recharts'
import { searchNutrition, getNutrition } from '../services/api'
import type { NutritionData, FoodSearchResult } from '../types'
import NutritionCard from '../components/NutritionCard'
import ErrorMessage from '../components/ErrorMessage'

function MacroDistributionCard({ data }: { data: NutritionData }) {
  const protein = data.protein ?? 0
  const carbs = data.carbohydrates ?? 0
  const fat = data.fat ?? 0
  const total = protein + carbs + fat

  const pPct = total > 0 ? Math.round((protein / total) * 100) : 0
  const cPct = total > 0 ? Math.round((carbs / total) * 100) : 0
  const fPct = total > 0 ? Math.max(0, 100 - pPct - cPct) : 0

  const chartData = [
    { name: 'Protein', value: Number(protein.toFixed(1)), color: '#3b82f6' },
    { name: 'Carbs', value: Number(carbs.toFixed(1)), color: '#f59e0b' },
    { name: 'Total Fat', value: Number(fat.toFixed(1)), color: '#a855f7' },
  ].filter((d) => d.value > 0)

  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
      <div className="flex items-center gap-2 mb-4">
        <div className="w-8 h-8 rounded-lg bg-[#e8f4ed] text-[#2d6a4f] flex items-center justify-center font-bold">
          <PieIcon className="w-4 h-4" />
        </div>
        <div>
          <h4 className="font-bold text-gray-900 text-sm">Macro Distribution</h4>
          <p className="text-xs text-gray-500">Ratio by macronutrient mass</p>
        </div>
      </div>

      {total > 0 ? (
        <div>
          <div className="h-44 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={chartData}
                  cx="50%"
                  cy="50%"
                  innerRadius={45}
                  outerRadius={70}
                  paddingAngle={3}
                  dataKey="value"
                >
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(val: unknown) => [`${val}g`, 'Amount']}
                  contentStyle={{ borderRadius: '0.75rem', border: '1px solid #e5e7eb', fontSize: '12px' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Visual Ratio Bar */}
          <div className="h-2.5 w-full flex rounded-full overflow-hidden my-3 bg-gray-100">
            {pPct > 0 && <div style={{ width: `${pPct}%` }} className="bg-blue-500" title={`Protein: ${pPct}%`} />}
            {cPct > 0 && <div style={{ width: `${cPct}%` }} className="bg-amber-500" title={`Carbs: ${cPct}%`} />}
            {fPct > 0 && <div style={{ width: `${fPct}%` }} className="bg-purple-500" title={`Fat: ${fPct}%`} />}
          </div>

          {/* Legends */}
          <div className="grid grid-cols-3 gap-2 pt-2 text-center text-xs">
            <div className="p-2 rounded-xl bg-blue-50/70 border border-blue-100">
              <span className="block font-semibold text-blue-700">Protein</span>
              <span className="font-bold text-gray-900 text-sm">{protein.toFixed(1)}g</span>
              <span className="block text-[11px] text-blue-600/80">{pPct}%</span>
            </div>
            <div className="p-2 rounded-xl bg-amber-50/70 border border-amber-100">
              <span className="block font-semibold text-amber-700">Carbs</span>
              <span className="font-bold text-gray-900 text-sm">{carbs.toFixed(1)}g</span>
              <span className="block text-[11px] text-amber-600/80">{cPct}%</span>
            </div>
            <div className="p-2 rounded-xl bg-purple-50/70 border border-purple-100">
              <span className="block font-semibold text-purple-700">Fat</span>
              <span className="font-bold text-gray-900 text-sm">{fat.toFixed(1)}g</span>
              <span className="block text-[11px] text-purple-600/80">{fPct}%</span>
            </div>
          </div>
        </div>
      ) : (
        <p className="text-xs text-gray-400 text-center py-6">Macronutrient data not available for this food item.</p>
      )}
    </div>
  )
}

function ServingSourceSummaryCard({ data }: { data: NutritionData }) {
  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
      <div className="flex items-center gap-2 mb-4">
        <div className="w-8 h-8 rounded-lg bg-[#e8f4ed] text-[#2d6a4f] flex items-center justify-center font-bold">
          <Database className="w-4 h-4" />
        </div>
        <div>
          <h4 className="font-bold text-gray-900 text-sm">Serving & Source Details</h4>
          <p className="text-xs text-gray-500">USDA FoodData Central Reference</p>
        </div>
      </div>

      <div className="space-y-3 text-sm">
        <div className="flex justify-between items-center py-2 border-b border-gray-50">
          <span className="text-gray-500 text-xs">Standard Basis</span>
          <span className="font-semibold text-gray-800 text-xs bg-gray-100 px-2 py-0.5 rounded">
            {data.basis || 'Per 100g'}
          </span>
        </div>
        <div className="flex justify-between items-center py-2 border-b border-gray-50">
          <span className="text-gray-500 text-xs">Serving Size</span>
          <span className="font-semibold text-gray-800 text-xs">
            {data.serving_size
              ? `${data.serving_size} ${data.serving_size_unit || 'g'}`
              : '100 g (Default Standard)'}
          </span>
        </div>
        <div className="flex justify-between items-center py-2 border-b border-gray-50">
          <span className="text-gray-500 text-xs">Data Source</span>
          <span className="font-medium text-emerald-800 text-xs bg-emerald-50 px-2 py-0.5 rounded flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3 text-emerald-600" />
            {data.source || 'USDA FoodData Central'}
          </span>
        </div>
        {data.fdcId && (
          <div className="flex justify-between items-center py-2 border-b border-gray-50">
            <span className="text-gray-500 text-xs">FDC Record ID</span>
            <a
              href={`https://fdc.nal.usda.gov/food-details/${data.fdcId}/nutrients`}
              target="_blank"
              rel="noopener noreferrer"
              className="font-mono text-xs text-[#2d6a4f] hover:underline flex items-center gap-1 font-semibold"
            >
              #{data.fdcId}
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        )}
        {data.calories != null && (
          <div className="flex justify-between items-center pt-1">
            <span className="text-gray-500 text-xs">Energy Density</span>
            <span className="font-bold text-orange-600 text-xs">
              {Math.round(data.calories)} kcal / 100g
            </span>
          </div>
        )}
      </div>
    </div>
  )
}

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
    <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      {/* Search Header - Centered */}
      <div className="max-w-3xl mx-auto mb-6">
        <form onSubmit={handleSearch} className="flex gap-3">
          <div className="flex-1 relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search for a food (e.g., pizza, chicken, apple)"
              className="w-full pl-12 pr-4 py-3 rounded-xl border border-gray-200 bg-white text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-[#52b788] focus:border-transparent transition-all shadow-2xs"
            />
          </div>
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="px-6 py-3 bg-[#2d6a4f] hover:bg-[#1a3d2b] disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold rounded-xl transition-all flex items-center gap-2 shadow-2xs"
          >
            {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Search className="w-5 h-5" />}
            Search
          </button>
        </form>
      </div>

      {error && (
        <div className="max-w-3xl mx-auto mb-6">
          <ErrorMessage message={error} />
        </div>
      )}

      {/* Search results */}
      {searchResults.length > 0 && !nutrition && (
        <div className="max-w-3xl mx-auto bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden mb-6">
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
                <span className="text-xs text-[#2d6a4f] bg-[#e8f4ed] px-2 py-1 rounded-lg mt-1 flex-shrink-0 font-medium">FDC #{food.fdcId}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {detailLoading && (
        <div className="max-w-3xl mx-auto bg-white rounded-2xl border border-gray-100 shadow-sm p-8 mb-6">
          <div className="flex items-center gap-3 justify-center">
            <Loader2 className="w-6 h-6 text-[#2d6a4f] animate-spin" />
            <span className="text-gray-600">Retrieving nutrition data...</span>
          </div>
        </div>
      )}

      {/* Results 2-Column Split */}
      {nutrition && (
        <div className="space-y-4">
          <button
            onClick={() => { setNutrition(null) }}
            className="inline-flex items-center gap-1.5 text-sm text-[#2d6a4f] hover:text-[#1a3d2b] font-medium transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to search results
          </button>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            {/* Left Column: Nutrition Breakdown Card */}
            <div className="lg:col-span-7">
              <NutritionCard data={nutrition} />
            </div>

            {/* Right Column: Macro Distribution & Serving/Source Summary */}
            <div className="lg:col-span-5 space-y-6">
              <MacroDistributionCard data={nutrition} />
              <ServingSourceSummaryCard data={nutrition} />
            </div>
          </div>
        </div>
      )}

      {!searched && (
        <div className="max-w-2xl mx-auto bg-[#e8f4ed] rounded-2xl p-8 text-center mt-4">
          <Search className="w-12 h-12 text-[#2d6a4f] mx-auto mb-4" />
          <p className="text-[#2d6a4f] font-semibold">Search for any food</p>
          <p className="text-sm text-[#40916c] mt-2">Try: pizza, chicken curry, apple, brown rice...</p>
        </div>
      )}
    </div>
  )
}
