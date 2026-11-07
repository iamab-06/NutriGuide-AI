import { useState } from 'react'
import { GitCompare, Loader2, TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { compareFoods } from '../services/api'
import type { CompareResponse } from '../types'
import ErrorMessage from '../components/ErrorMessage'

interface NutrientCompareRow {
  label: string
  unit: string
  value1: number | null | undefined
  value2: number | null | undefined
}

function getWinner(v1: number | null | undefined, v2: number | null | undefined, higherIsBetter: boolean) {
  if (v1 == null || v2 == null) return null
  if (Math.abs(v1 - v2) < 0.5) return 'tie'
  if (higherIsBetter) return v1 > v2 ? 'food1' : 'food2'
  return v1 < v2 ? 'food1' : 'food2'
}

function CompareRow({ label, unit, value1, value2 }: NutrientCompareRow) {
  // For protein & fiber, higher is better. For calories, fat, sugar, sodium — lower.
  const higherBetter = ['Protein', 'Fiber'].includes(label)
  const winner = getWinner(value1, value2, higherBetter)

  const fmt = (v: number | null | undefined) =>
    v != null ? `${v % 1 === 0 ? v : v.toFixed(1)} ${unit}` : '—'

  const cell = (v: number | null | undefined, side: 'food1' | 'food2') => {
    const isWinner = winner === side
    const isTie = winner === 'tie'
    return (
      <td className={`py-3 px-4 text-center text-sm font-semibold ${
        v == null ? 'text-gray-300' :
        isTie ? 'text-gray-600' :
        isWinner ? 'text-green-700 bg-green-50' : 'text-gray-500'
      }`}>
        <div className="flex items-center justify-center gap-1">
          {fmt(v)}
          {v != null && !isTie && (
            isWinner
              ? <TrendingUp className="w-3.5 h-3.5 text-green-500" />
              : <TrendingDown className="w-3.5 h-3.5 text-red-400" />
          )}
          {v != null && isTie && <Minus className="w-3.5 h-3.5 text-gray-400" />}
        </div>
      </td>
    )
  }

  return (
    <tr className="border-b border-gray-50 last:border-0 hover:bg-gray-50/50">
      <td className="py-3 px-4 text-sm text-gray-600">{label}</td>
      {cell(value1, 'food1')}
      {cell(value2, 'food2')}
    </tr>
  )
}

const POPULAR_COMPARISONS = [
  { food1: 'pizza', food2: 'hamburger' },
  { food1: 'chicken curry', food2: 'fried rice' },
  { food1: 'caesar salad', food2: 'french fries' },
  { food1: 'steak', food2: 'sushi' },
]

export default function CompareFoods() {
  const [food1, setFood1] = useState('')
  const [food2, setFood2] = useState('')
  const [result, setResult] = useState<CompareResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleCompare = async (f1 = food1, f2 = food2) => {
    if (!f1.trim() || !f2.trim()) return
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const data = await compareFoods(f1.trim(), f2.trim())
      setResult(data)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Comparison failed.')
    } finally {
      setLoading(false)
    }
  }

  const rows: NutrientCompareRow[] = result
    ? [
        { label: 'Calories', unit: 'kcal', value1: result.food1.calories, value2: result.food2.calories },
        { label: 'Protein', unit: 'g', value1: result.food1.protein, value2: result.food2.protein },
        { label: 'Carbohydrates', unit: 'g', value1: result.food1.carbohydrates, value2: result.food2.carbohydrates },
        { label: 'Total Fat', unit: 'g', value1: result.food1.fat, value2: result.food2.fat },
        { label: 'Sugar', unit: 'g', value1: result.food1.sugar, value2: result.food2.sugar },
        { label: 'Fiber', unit: 'g', value1: result.food1.fiber, value2: result.food2.fiber },
        { label: 'Sodium', unit: 'mg', value1: result.food1.sodium, value2: result.food2.sodium },
        { label: 'Cholesterol', unit: 'mg', value1: result.food1.cholesterol, value2: result.food2.cholesterol },
      ]
    : []

  return (
    <div className="p-6 lg:p-8 max-w-5xl mx-auto">
      {/* Input */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 mb-6">
        <div className="grid grid-cols-1 sm:grid-cols-[1fr_auto_1fr] gap-4 items-end">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Food 1</label>
            <input
              type="text"
              value={food1}
              onChange={(e) => setFood1(e.target.value)}
              placeholder="e.g., pizza"
              className="w-full px-4 py-3 rounded-xl border border-gray-200 bg-gray-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#52b788] focus:border-transparent transition-all"
            />
          </div>
          <div className="flex items-center justify-center pb-1">
            <div className="w-10 h-10 rounded-full bg-[#e8f4ed] flex items-center justify-center">
              <GitCompare className="w-5 h-5 text-[#2d6a4f]" />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Food 2</label>
            <input
              type="text"
              value={food2}
              onChange={(e) => setFood2(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleCompare()}
              placeholder="e.g., hamburger"
              className="w-full px-4 py-3 rounded-xl border border-gray-200 bg-gray-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#52b788] focus:border-transparent transition-all"
            />
          </div>
        </div>
        <button
          onClick={() => handleCompare()}
          disabled={loading || !food1.trim() || !food2.trim()}
          className="mt-4 w-full py-3 bg-[#2d6a4f] hover:bg-[#1a3d2b] disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold rounded-xl transition-all flex items-center justify-center gap-2"
        >
          {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <GitCompare className="w-5 h-5" />}
          Compare Foods
        </button>

        {/* Popular comparisons */}
        <div className="mt-4">
          <p className="text-xs text-gray-500 mb-2">Popular comparisons:</p>
          <div className="flex flex-wrap gap-2">
            {POPULAR_COMPARISONS.map(({ food1: f1, food2: f2 }) => (
              <button
                key={`${f1}-${f2}`}
                onClick={() => {
                  setFood1(f1)
                  setFood2(f2)
                  handleCompare(f1, f2)
                }}
                disabled={loading}
                className="px-3 py-1.5 text-xs font-medium bg-[#e8f4ed] text-[#2d6a4f] rounded-full hover:bg-[#b7e4c7] transition-all disabled:opacity-50"
              >
                {f1} vs {f2}
              </button>
            ))}
          </div>
        </div>
      </div>

      {error && <ErrorMessage message={error} onRetry={() => handleCompare()} />}

      {loading && (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-12 text-center">
          <Loader2 className="w-10 h-10 text-[#2d6a4f] animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Fetching nutrition data and generating comparison...</p>
        </div>
      )}

      {result && !loading && (
        <div className="space-y-6">
          {/* Comparison table */}
          <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
            <div className="grid grid-cols-[1fr_1fr_1fr] bg-[#0d2818] text-white">
              <div className="px-4 py-4 text-sm font-medium text-green-200">Nutrient (per 100g)</div>
              <div className="px-4 py-4 text-center font-bold">
                <p className="text-[#52b788] text-xs uppercase tracking-wide mb-0.5">Food 1</p>
                <p className="text-sm leading-tight">{result.food1.food_name}</p>
              </div>
              <div className="px-4 py-4 text-center font-bold">
                <p className="text-[#52b788] text-xs uppercase tracking-wide mb-0.5">Food 2</p>
                <p className="text-sm leading-tight">{result.food2.food_name}</p>
              </div>
            </div>
            <table className="w-full">
              <tbody>
                {rows.map((row) => (
                  <CompareRow key={row.label} {...row} />
                ))}
              </tbody>
            </table>
            <div className="px-4 py-3 bg-gray-50 border-t border-gray-100">
              <p className="text-xs text-gray-400">
                Data from USDA FoodData Central &bull; Basis: {result.basis} &bull;
                <TrendingUp className="w-3 h-3 inline ml-1 text-green-500" /> = better value for this nutrient
              </p>
            </div>
          </div>

          {/* AI Summary */}
          {result.ai_summary && (
            <div className="bg-gradient-to-br from-[#0d2818] to-[#2d6a4f] rounded-2xl p-6 text-white">
              <div className="flex items-center gap-2 mb-3">
                <div className="w-7 h-7 rounded-lg bg-[#52b788] flex items-center justify-center">
                  <GitCompare className="w-4 h-4 text-white" />
                </div>
                <h3 className="font-bold">AI Comparison Summary</h3>
                <span className="text-xs text-green-300 ml-auto">Powered by Gemma 3 4B</span>
              </div>
              <p className="text-green-100 text-sm leading-relaxed">{result.ai_summary}</p>
              <p className="text-green-300/60 text-xs mt-3">
                This summary is based solely on the USDA nutrition data above. It is not medical advice.
              </p>
            </div>
          )}

          {result.comparison_notes && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-2xl p-4">
              <p className="text-sm text-yellow-700">{result.comparison_notes}</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
