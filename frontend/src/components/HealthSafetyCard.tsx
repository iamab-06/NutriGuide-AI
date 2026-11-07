import { useState } from 'react'
import {
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  Info,
} from 'lucide-react'
import type { HealthSafetyReport } from '../types'

interface Props {
  report: HealthSafetyReport
  foodName?: string
}

export default function HealthSafetyCard({ report, foodName }: Props) {
  const [expanded, setExpanded] = useState(true)

  if (!report || !report.evaluations || report.evaluations.length === 0) {
    return null
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'SAFE':
        return {
          bg: 'bg-emerald-50 border-emerald-200 text-emerald-800',
          indicator: 'bg-emerald-500',
          label: 'Safe & Recommended',
          icon: <ShieldCheck className="w-5 h-5 text-emerald-600" />,
        }
      case 'MODERATE':
        return {
          bg: 'bg-amber-50 border-amber-200 text-amber-800',
          indicator: 'bg-amber-500',
          label: 'Moderate / Portion Control',
          icon: <AlertTriangle className="w-5 h-5 text-amber-600" />,
        }
      case 'RESTRICTED':
      default:
        return {
          bg: 'bg-rose-50 border-rose-200 text-rose-800',
          indicator: 'bg-rose-500',
          label: 'Caution / Restricted',
          icon: <ShieldAlert className="w-5 h-5 text-rose-600" />,
        }
    }
  }

  const overall = getStatusBadge(report.overall_status)

  return (
    <div className={`rounded-2xl border ${overall.bg} p-5 mb-6 shadow-xs transition-all`}>
      {/* Top Banner */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <div className="p-2 bg-white rounded-xl shadow-2xs flex-shrink-0 mt-0.5">
            {overall.icon}
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xs uppercase tracking-wider font-bold text-gray-500">
                Clinical Health Advisor
              </span>
              <span
                className={`text-xs px-2.5 py-0.5 rounded-full font-bold flex items-center gap-1.5 ${
                  report.overall_status === 'SAFE'
                    ? 'bg-emerald-100 text-emerald-800'
                    : report.overall_status === 'MODERATE'
                    ? 'bg-amber-100 text-amber-800'
                    : 'bg-rose-100 text-rose-800'
                }`}
              >
                <span className={`w-2 h-2 rounded-full ${overall.indicator}`}></span>
                {overall.label}
              </span>
            </div>
            <h4 className="text-base font-bold text-gray-900 mt-1">
              {foodName ? `Health Impact: ${foodName}` : 'Health Condition Screening'}
            </h4>
            <p className="text-xs text-gray-700 mt-1 leading-relaxed">{report.summary}</p>
          </div>
        </div>

        <button
          type="button"
          onClick={() => setExpanded(!expanded)}
          className="text-xs font-semibold px-2.5 py-1 rounded-lg bg-white/80 hover:bg-white text-gray-700 border border-gray-200 flex items-center gap-1 flex-shrink-0 transition-colors"
        >
          <span>{expanded ? 'Hide Details' : 'View Details'}</span>
          {expanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </button>
      </div>

      {/* Expanded Breakdown */}
      {expanded && (
        <div className="mt-4 pt-4 border-t border-gray-200/60 space-y-3">
          {report.evaluations.map((ev) => {
            return (
              <div
                key={ev.condition_id}
                className="bg-white/95 rounded-xl border border-gray-200/80 p-3.5 shadow-2xs"
              >
                <div className="flex items-center justify-between gap-2 mb-1.5">
                  <span className="font-bold text-xs text-gray-900">{ev.condition_name}</span>
                  <span
                    className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                      ev.status === 'SAFE'
                        ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                        : ev.status === 'MODERATE'
                        ? 'bg-amber-50 text-amber-700 border border-amber-200'
                        : 'bg-rose-50 text-rose-700 border border-rose-200'
                    }`}
                  >
                    {ev.status}
                  </span>
                </div>
                <p className="text-xs font-semibold text-gray-800 mb-0.5">{ev.headline}</p>
                <p className="text-xs text-gray-600 leading-relaxed">{ev.explanation}</p>
                {ev.recommendation && (
                  <div className="mt-2 text-xs bg-gray-50 border-l-2 border-[#2d6a4f] pl-2.5 py-1 text-gray-700">
                    <span className="font-semibold text-[#2d6a4f]">Recommendation: </span>
                    {ev.recommendation}
                  </div>
                )}
              </div>
            )
          })}

          <div className="flex items-center gap-1.5 text-[11px] text-gray-500 pt-1">
            <Info className="w-3.5 h-3.5 flex-shrink-0 text-gray-400" />
            <span>{report.disclaimer}</span>
          </div>
        </div>
      )}
    </div>
  )
}
