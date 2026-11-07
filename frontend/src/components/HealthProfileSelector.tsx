import { useState, useEffect } from 'react'
import {
  Heart,
  Activity,
  ShieldCheck,
  AlertCircle,
  Wheat,
  Milk,
  Flame,
  Check,
  SlidersHorizontal,
  ChevronDown,
  ChevronUp,
} from 'lucide-react'
import { getHealthConditions } from '../services/api'
import type { ConditionItem } from '../types'

const FALLBACK_CONDITIONS: ConditionItem[] = [
  {
    id: 'diabetes',
    name: 'Diabetes / Pre-diabetes',
    category: 'Metabolic',
    icon: 'Activity',
    description: 'Monitors sugar, net carbohydrates, dietary fiber, and glycemic spikes.',
  },
  {
    id: 'hypertension',
    name: 'Hypertension (High BP)',
    category: 'Cardiovascular',
    icon: 'Heart',
    description: 'Screens sodium against WHO & ICMR 2000mg daily ceiling.',
  },
  {
    id: 'hyperlipidemia',
    name: 'High Cholesterol',
    category: 'Cardiovascular',
    icon: 'ShieldCheck',
    description: 'Evaluates atherogenic saturated fats and dietary cholesterol.',
  },
  {
    id: 'gout_uric_acid',
    name: 'High Uric Acid / Gout',
    category: 'Metabolic',
    icon: 'AlertCircle',
    description: 'Flags purine-rich meats and flare-up risk factors.',
  },
  {
    id: 'celiac_gluten',
    name: 'Gluten / Celiac',
    category: 'Gastrointestinal',
    icon: 'Wheat',
    description: 'Detects wheat, maida, semolina, barley, and hidden gluten.',
  },
  {
    id: 'lactose_intolerance',
    name: 'Lactose Intolerance',
    category: 'Gastrointestinal',
    icon: 'Milk',
    description: 'Screens for milk, paneer, and unfermented dairy.',
  },
  {
    id: 'weight_management',
    name: 'Calorie Deficit / Weight Loss',
    category: 'Lifestyle',
    icon: 'Flame',
    description: 'Screens energy density and satiety (protein + fiber).',
  },
]

interface Props {
  selectedConditions: string[]
  onChange: (conditions: string[]) => void
}

export default function HealthProfileSelector({ selectedConditions, onChange }: Props) {
  const [conditions, setConditions] = useState<ConditionItem[]>(FALLBACK_CONDITIONS)
  const [isOpen, setIsOpen] = useState(false)

  useEffect(() => {
    getHealthConditions()
      .then((data) => {
        if (Array.isArray(data) && data.length > 0) {
          setConditions(data)
        }
      })
      .catch(() => {
        // Fallback already preset
      })
  }, [])

  const toggleCondition = (id: string) => {
    let next: string[]
    if (selectedConditions.includes(id)) {
      next = selectedConditions.filter((c) => c !== id)
    } else {
      next = [...selectedConditions, id]
    }
    onChange(next)
    try {
      localStorage.setItem('nutriguide_active_conditions', JSON.stringify(next))
    } catch {
      // ignore
    }
  }

  const renderIcon = (iconName: string) => {
    switch (iconName) {
      case 'Activity':
        return <Activity className="w-3.5 h-3.5 text-blue-500" />
      case 'Heart':
        return <Heart className="w-3.5 h-3.5 text-rose-500" />
      case 'ShieldCheck':
        return <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
      case 'AlertCircle':
        return <AlertCircle className="w-3.5 h-3.5 text-amber-500" />
      case 'Wheat':
        return <Wheat className="w-3.5 h-3.5 text-yellow-600" />
      case 'Milk':
        return <Milk className="w-3.5 h-3.5 text-indigo-500" />
      case 'Flame':
        return <Flame className="w-3.5 h-3.5 text-orange-500" />
      default:
        return <Activity className="w-3.5 h-3.5 text-gray-500" />
    }
  }

  return (
    <div className="bg-white border border-gray-200/80 rounded-2xl shadow-xs overflow-hidden mb-6 transition-all">
      {/* Header bar */}
      <div
        onClick={() => setIsOpen(!isOpen)}
        className="px-5 py-3.5 flex items-center justify-between cursor-pointer hover:bg-gray-50/70 transition-colors select-none"
      >
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-[#e8f4ed] text-[#2d6a4f] flex items-center justify-center font-bold">
            <SlidersHorizontal className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-bold text-gray-900">
                Personal Health & Dietary Profile
              </span>
              {selectedConditions.length > 0 ? (
                <span className="px-2 py-0.5 bg-[#2d6a4f] text-white text-xs font-semibold rounded-full">
                  {selectedConditions.length} active
                </span>
              ) : (
                <span className="text-xs text-gray-400">None selected</span>
              )}
            </div>
            <p className="text-xs text-gray-500">
              NutriGuide evaluates foods against your active clinical conditions (Diabetes, BP, Heart, etc.).
            </p>
          </div>
        </div>

        <button
          type="button"
          className="text-gray-400 hover:text-gray-600 p-1"
          title={isOpen ? 'Collapse health settings' : 'Expand health settings'}
        >
          {isOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>
      </div>

      {/* Quick pills bar (always visible) */}
      <div className="px-5 pb-3 flex flex-wrap gap-1.5 border-t border-gray-100 pt-2.5 bg-gray-50/50">
        {conditions.map((cond) => {
          const active = selectedConditions.includes(cond.id)
          return (
            <button
              key={cond.id}
              type="button"
              onClick={() => toggleCondition(cond.id)}
              className={`px-3 py-1.5 rounded-xl text-xs font-medium flex items-center gap-1.5 transition-all border ${
                active
                  ? 'bg-[#2d6a4f] text-white border-[#2d6a4f] shadow-xs'
                  : 'bg-white text-gray-700 border-gray-200 hover:border-[#52b788] hover:bg-[#e8f4ed]/50'
              }`}
            >
              {active ? <Check className="w-3.5 h-3.5 text-emerald-300" /> : renderIcon(cond.icon)}
              <span>{cond.name}</span>
            </button>
          )
        })}
      </div>

      {/* Expanded details view */}
      {isOpen && (
        <div className="p-5 border-t border-gray-100 bg-white grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
          {conditions.map((cond) => {
            const active = selectedConditions.includes(cond.id)
            return (
              <div
                key={cond.id}
                onClick={() => toggleCondition(cond.id)}
                className={`p-3 rounded-xl border cursor-pointer transition-all ${
                  active
                    ? 'border-[#2d6a4f] bg-[#f8fdf9] ring-1 ring-[#2d6a4f]/20'
                    : 'border-gray-200 hover:border-gray-300 bg-gray-50/30'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-1.5">
                    {renderIcon(cond.icon)}
                    <span className="font-bold text-gray-900">{cond.name}</span>
                  </div>
                  <span
                    className={`w-4 h-4 rounded-full flex items-center justify-center text-[10px] ${
                      active ? 'bg-[#2d6a4f] text-white font-bold' : 'border border-gray-300'
                    }`}
                  >
                    {active && '✓'}
                  </span>
                </div>
                <p className="text-gray-600 leading-relaxed">{cond.description}</p>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
