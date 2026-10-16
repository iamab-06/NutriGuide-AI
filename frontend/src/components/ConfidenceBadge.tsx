interface Props {
  confidence: number
  isConfident: boolean
}

export default function ConfidenceBadge({ confidence, isConfident }: Props) {
  const pct = Math.round(confidence * 100)
  const color = isConfident
    ? pct >= 75 ? 'bg-green-100 text-green-800 border-green-200'
    : 'bg-blue-100 text-blue-800 border-blue-200'
    : 'bg-yellow-100 text-yellow-800 border-yellow-200'

  return (
    <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-semibold border ${color}`}>
      <span className={`w-2 h-2 rounded-full ${isConfident ? 'bg-green-500' : 'bg-yellow-500'}`} />
      {pct}% confidence
    </span>
  )
}
