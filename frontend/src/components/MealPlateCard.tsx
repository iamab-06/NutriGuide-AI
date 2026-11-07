import { useState } from 'react'
import {
  UtensilsCrossed,
  PieChart,
  Flame,
  Dna,
  Wheat,
  Droplet,
  Layers,
  Sparkles,
  Plus,
  Minus,
} from 'lucide-react'
import type { MealPlateAnalysis, MealComponent } from '../types'
import HealthSafetyCard from './HealthSafetyCard'

interface Props {
  analysis: MealPlateAnalysis
}

export default function MealPlateCard({ analysis }: Props) {
  // Allow user to dynamically tweak item portions live
  const [components, setComponents] = useState<MealComponent[]>(analysis.components || [])

  const updatePortion = (index: number, deltaG: number) => {
    setComponents((prev) => {
      const copy = [...prev]
      const target = copy[index]
      if (!target) return prev

      const currentPortion = target.portion_g
      const nextPortion = Math.max(20, Math.min(600, currentPortion + deltaG))
      const ratio = nextPortion / currentPortion

      copy[index] = {
        ...target,
        portion_g: nextPortion,
        serving_description: `${nextPortion.toFixed(0)}g portion`,
        calories: Math.round(target.calories * ratio * 10) / 10,
        protein: Math.round(target.protein * ratio * 10) / 10,
        carbohydrates: Math.round(target.carbohydrates * ratio * 10) / 10,
        fat: Math.round(target.fat * ratio * 10) / 10,
        fiber: target.fiber ? Math.round(target.fiber * ratio * 10) / 10 : 0,
        sugar: target.sugar ? Math.round(target.sugar * ratio * 10) / 10 : 0,
        sodium: target.sodium ? Math.round(target.sodium * ratio * 10) / 10 : 0,
      }
      return copy
    })
  }

  // Recalculate totals dynamically
  const totalCalories = Math.round(components.reduce((acc, c) => acc + (c.calories || 0), 0))
  const totalProtein = Math.round(components.reduce((acc, c) => acc + (c.protein || 0), 0) * 10) / 10
  const totalCarbs = Math.round(components.reduce((acc, c) => acc + (c.carbohydrates || 0), 0) * 10) / 10
  const totalFat = Math.round(components.reduce((acc, c) => acc + (c.fat || 0), 0) * 10) / 10
  const totalFiber = Math.round(components.reduce((acc, c) => acc + (c.fiber || 0), 0) * 10) / 10
  const totalSodium = Math.round(components.reduce((acc, c) => acc + (c.sodium || 0), 0))

  const totalCalSafe = Math.max(1, totalCalories)
  const carbPct = Math.round(((totalCarbs * 4) / totalCalSafe) * 100)
  const protPct = Math.round(((totalProtein * 4) / totalCalSafe) * 100)
  const fatPct = Math.max(0, 100 - carbPct - protPct)

  return (
    <div className="space-y-6">
      {/* Plate Header & Total Nutrition Summary */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
        {/* Top Header */}
        <div className="bg-gradient-to-r from-[#1a3d2b] to-[#2d6a4f] text-white p-6">
          <div className="flex items-center justify-between gap-4 flex-wrap">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-white/10 flex items-center justify-center backdrop-blur-xs">
                <UtensilsCrossed className="w-5 h-5 text-emerald-300" />
              </div>
              <div>
                <span className="text-xs font-semibold text-emerald-200 uppercase tracking-wider block">
                  Multi-Item Meal Decomposition
                </span>
                <h3 className="text-xl font-bold">{analysis.meal_title}</h3>
              </div>
            </div>
            <span className="px-3 py-1 bg-white/20 text-white rounded-full text-xs font-medium backdrop-blur-xs">
              {components.length} Items Identified
            </span>
          </div>

          {analysis.visual_summary && (
            <p className="text-xs text-emerald-100/90 mt-3 leading-relaxed">
              {analysis.visual_summary}
            </p>
          )}

          {/* Aggregated Macro Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5 mt-5">
            <div className="bg-white/10 rounded-xl p-3 backdrop-blur-xs">
              <div className="flex items-center gap-1.5 text-xs text-emerald-200 mb-0.5">
                <Flame className="w-3.5 h-3.5 text-orange-400" />
                <span>Total Energy</span>
              </div>
              <p className="text-lg font-bold text-white">{totalCalories} <span className="text-xs font-normal">kcal</span></p>
            </div>

            <div className="bg-white/10 rounded-xl p-3 backdrop-blur-xs">
              <div className="flex items-center gap-1.5 text-xs text-emerald-200 mb-0.5">
                <Dna className="w-3.5 h-3.5 text-blue-300" />
                <span>Protein</span>
              </div>
              <p className="text-lg font-bold text-white">{totalProtein} <span className="text-xs font-normal">g</span></p>
            </div>

            <div className="bg-white/10 rounded-xl p-3 backdrop-blur-xs">
              <div className="flex items-center gap-1.5 text-xs text-emerald-200 mb-0.5">
                <Wheat className="w-3.5 h-3.5 text-yellow-300" />
                <span>Carbohydrates</span>
              </div>
              <p className="text-lg font-bold text-white">{totalCarbs} <span className="text-xs font-normal">g</span></p>
            </div>

            <div className="bg-white/10 rounded-xl p-3 backdrop-blur-xs">
              <div className="flex items-center gap-1.5 text-xs text-emerald-200 mb-0.5">
                <Droplet className="w-3.5 h-3.5 text-rose-300" />
                <span>Total Fat</span>
              </div>
              <p className="text-lg font-bold text-white">{totalFat} <span className="text-xs font-normal">g</span></p>
            </div>

            <div className="bg-white/10 rounded-xl p-3 backdrop-blur-xs">
              <div className="flex items-center gap-1.5 text-xs text-emerald-200 mb-0.5">
                <Layers className="w-3.5 h-3.5 text-teal-300" />
                <span>Dietary Fiber</span>
              </div>
              <p className="text-lg font-bold text-white">{totalFiber} <span className="text-xs font-normal">g</span></p>
            </div>

            <div className="bg-white/10 rounded-xl p-3 backdrop-blur-xs">
              <div className="flex items-center gap-1.5 text-xs text-emerald-200 mb-0.5">
                <PieChart className="w-3.5 h-3.5 text-purple-300" />
                <span>Sodium</span>
              </div>
              <p className="text-lg font-bold text-white">{totalSodium} <span className="text-xs font-normal">mg</span></p>
            </div>
          </div>

          {/* Macro Calorie Energy Bar */}
          <div className="mt-4 pt-3 border-t border-white/15">
            <div className="flex items-center justify-between text-xs text-emerald-100 mb-1.5 font-medium">
              <span>Macro Calorie Split</span>
              <div className="flex gap-3">
                <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-blue-400"></span>Protein {protPct}%</span>
                <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-yellow-400"></span>Carbs {carbPct}%</span>
                <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-rose-400"></span>Fat {fatPct}%</span>
              </div>
            </div>
            <div className="w-full h-2.5 bg-white/20 rounded-full overflow-hidden flex">
              <div style={{ width: `${protPct}%` }} className="bg-blue-400 h-full transition-all" title="Protein"></div>
              <div style={{ width: `${carbPct}%` }} className="bg-yellow-400 h-full transition-all" title="Carbohydrates"></div>
              <div style={{ width: `${fatPct}%` }} className="bg-rose-400 h-full transition-all" title="Fat"></div>
            </div>
          </div>
        </div>

        {/* Itemized Components List */}
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h4 className="font-bold text-gray-900 text-sm flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-[#2d6a4f]" />
              Identified Plate Components & Portion Adjustment
            </h4>
            <span className="text-xs text-gray-500">
              Use (- / +) to tune portions to your actual plate
            </span>
          </div>

          <div className="space-y-3">
            {components.map((item, idx) => (
              <div
                key={idx}
                className="bg-gray-50/70 border border-gray-200/80 rounded-xl p-3.5 hover:bg-white hover:shadow-xs transition-all"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  {/* Name and description */}
                  <div className="flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-bold text-gray-900 text-sm">{item.name}</span>
                      <span className="text-xs px-2 py-0.5 rounded-full bg-[#e8f4ed] text-[#2d6a4f] font-medium">
                        {item.serving_description}
                      </span>
                    </div>
                    {item.notes && (
                      <p className="text-xs text-gray-500 mt-0.5">{item.notes}</p>
                    )}
                  </div>

                  {/* Portion control buttons */}
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <span className="text-xs text-gray-500 font-medium">Portion:</span>
                    <button
                      type="button"
                      onClick={() => updatePortion(idx, -25)}
                      className="w-7 h-7 rounded-lg border border-gray-200 bg-white hover:bg-gray-100 flex items-center justify-center text-gray-600 transition-colors"
                      title="Decrease portion"
                    >
                      <Minus className="w-3.5 h-3.5" />
                    </button>
                    <span className="text-xs font-bold text-gray-800 w-12 text-center">
                      {item.portion_g.toFixed(0)}g
                    </span>
                    <button
                      type="button"
                      onClick={() => updatePortion(idx, 25)}
                      className="w-7 h-7 rounded-lg border border-gray-200 bg-white hover:bg-gray-100 flex items-center justify-center text-gray-600 transition-colors"
                      title="Increase portion"
                    >
                      <Plus className="w-3.5 h-3.5" />
                    </button>
                  </div>

                  {/* Item Macro breakdown */}
                  <div className="flex items-center gap-3 text-xs bg-white px-3 py-1.5 rounded-lg border border-gray-200/70 flex-shrink-0">
                    <span className="font-bold text-[#2d6a4f]">{item.calories} kcal</span>
                    <span className="text-gray-300">|</span>
                    <span className="text-blue-700 font-medium">{item.protein}g P</span>
                    <span className="text-gray-300">|</span>
                    <span className="text-yellow-700 font-medium">{item.carbohydrates}g C</span>
                    <span className="text-gray-300">|</span>
                    <span className="text-rose-700 font-medium">{item.fat}g F</span>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <p className="text-xs text-gray-400 mt-4 text-center">
            ✦ Individual component nutrition retrieved from verified ICMR-NIN IFCT & USDA databases.
          </p>
        </div>
      </div>

      {/* Health Safety Evaluation for Meal Plate */}
      {analysis.health_safety && (
        <HealthSafetyCard
          report={analysis.health_safety}
          foodName={analysis.meal_title}
        />
      )}
    </div>
  )
}
