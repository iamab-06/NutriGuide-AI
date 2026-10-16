import { type NutritionData } from '../types'
import { AlertCircle, ExternalLink } from 'lucide-react'

interface Props {
  data: NutritionData
  compact?: boolean
}

function NutrientRow({ label, value, unit, color = 'gray' }: {
  label: string
  value: number | null | undefined
  unit: string
  color?: string
}) {
  const colorMap: Record<string, string> = {
    orange: 'bg-orange-50 text-orange-700',
    blue: 'bg-blue-50 text-blue-700',
    green: 'bg-green-50 text-green-700',
    red: 'bg-red-50 text-red-700',
    purple: 'bg-purple-50 text-purple-700',
    yellow: 'bg-yellow-50 text-yellow-700',
    gray: 'bg-gray-50 text-gray-700',
  }
  return (
    <div className="flex items-center justify-between py-2.5 border-b border-gray-50 last:border-0">
      <span className="text-sm text-gray-600">{label}</span>
      {value != null ? (
        <span className={`text-sm font-semibold px-2.5 py-0.5 rounded-full ${colorMap[color] || colorMap.gray}`}>
          {value % 1 === 0 ? value : value.toFixed(1)} {unit}
        </span>
      ) : (
        <span className="text-xs text-gray-400 italic">Not available</span>
      )}
    </div>
  )
}

export default function NutritionCard({ data, compact = false }: Props) {
  if (!data.data_available) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-2xl p-6">
        <div className="flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold text-yellow-800">Nutrition data not available</p>
            <p className="text-sm text-yellow-700 mt-1">{data.notes || 'No matching record found in USDA FoodData Central.'}</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
      <div className="bg-gradient-to-r from-[#2d6a4f] to-[#40916c] px-6 py-4">
        <h3 className="text-white font-bold text-lg truncate">{data.food_name}</h3>
        <div className="flex items-center gap-4 mt-1">
          <span className="text-green-100 text-sm">Basis: {data.basis}</span>
          {data.fdcId && (
            <a
              href={`https://fdc.nal.usda.gov/food-details/${data.fdcId}/nutrients`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-green-200 hover:text-white text-xs flex items-center gap-1 transition-colors"
            >
              USDA <ExternalLink className="w-3 h-3" />
            </a>
          )}
        </div>
      </div>

      {/* Calorie highlight */}
      {data.calories != null && (
        <div className="bg-orange-50 border-b border-orange-100 px-6 py-3 flex items-center justify-between">
          <span className="font-semibold text-orange-800">Calories</span>
          <span className="text-2xl font-bold text-orange-600">{Math.round(data.calories)}<span className="text-sm font-normal ml-1">kcal</span></span>
        </div>
      )}

      <div className="px-6 py-2">
        <NutrientRow label="Protein" value={data.protein} unit="g" color="blue" />
        <NutrientRow label="Carbohydrates" value={data.carbohydrates} unit="g" color="yellow" />
        {!compact && <NutrientRow label="Sugar" value={data.sugar} unit="g" color="red" />}
        <NutrientRow label="Total Fat" value={data.fat} unit="g" color="purple" />
        {!compact && <NutrientRow label="Saturated Fat" value={data.saturated_fat} unit="g" color="purple" />}
        <NutrientRow label="Fiber" value={data.fiber} unit="g" color="green" />
        <NutrientRow label="Sodium" value={data.sodium} unit="mg" color="gray" />
        {!compact && <NutrientRow label="Cholesterol" value={data.cholesterol} unit="mg" color="gray" />}
      </div>

      <div className="px-6 py-3 bg-gray-50 border-t border-gray-100">
        <p className="text-xs text-gray-400">Source: {data.source}</p>
      </div>
    </div>
  )
}
