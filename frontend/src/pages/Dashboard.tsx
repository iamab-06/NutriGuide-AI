import { useNavigate } from 'react-router-dom'
import { Camera, Search, BarChart3, ShieldAlert, MessageSquare, GitCompare, Leaf, Zap, TrendingUp } from 'lucide-react'

const features = [
  {
    icon: Camera,
    title: 'Food Recognition',
    description: 'Upload a food photo and our MobileNetV3 AI instantly identifies it from 20 categories.',
    color: 'from-green-500 to-emerald-600',
    bg: 'bg-green-50',
    path: '/analyze',
  },
  {
    icon: BarChart3,
    title: 'Nutrition Analysis',
    description: 'Get detailed nutritional data from USDA FoodData Central — calories, protein, carbs, and more.',
    color: 'from-blue-500 to-blue-600',
    bg: 'bg-blue-50',
    path: '/nutrition',
  },
  {
    icon: ShieldAlert,
    title: 'Allergen Awareness',
    description: 'Search packaged products for ingredient lists and declared allergen information via Open Food Facts.',
    color: 'from-orange-500 to-orange-600',
    bg: 'bg-orange-50',
    path: '/ingredients',
  },
  {
    icon: MessageSquare,
    title: 'AI Nutrition Assistant',
    description: 'Ask questions about any food. Our Gemini-powered assistant uses RAG to give evidence-grounded answers.',
    color: 'from-purple-500 to-purple-600',
    bg: 'bg-purple-50',
    path: '/assistant',
  },
  {
    icon: GitCompare,
    title: 'Food Comparison',
    description: 'Compare two foods side-by-side on a per-100g basis with AI-generated nutritional insights.',
    color: 'from-teal-500 to-teal-600',
    bg: 'bg-teal-50',
    path: '/compare',
  },
]

const stats = [
  { icon: Leaf, label: 'Food Categories', value: '20', sub: 'AI-recognized' },
  { icon: Zap, label: 'Data Source', value: 'USDA', sub: 'FoodData Central' },
  { icon: TrendingUp, label: 'AI Model', value: 'Gemini', sub: '+ RAG Pipeline' },
]

export default function Dashboard() {
  const navigate = useNavigate()
  return (
    <div className="p-6 lg:p-8 max-w-6xl mx-auto">
      {/* Hero */}
      <div className="bg-gradient-to-br from-[#0d2818] via-[#1a3d2b] to-[#2d6a4f] rounded-3xl p-8 lg:p-12 text-white mb-8 relative overflow-hidden">
        <div className="absolute inset-0 opacity-5">
          <div className="absolute top-4 right-4 w-64 h-64 rounded-full bg-white" />
          <div className="absolute -bottom-8 -left-8 w-48 h-48 rounded-full bg-white" />
        </div>
        <div className="relative">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-12 h-12 rounded-2xl bg-[#52b788] flex items-center justify-center">
              <Leaf className="w-7 h-7 text-white" />
            </div>
            <div>
              <h1 className="text-3xl lg:text-4xl font-bold">NutriGuide AI</h1>
              <p className="text-green-300 text-sm">Powered by Computer Vision & Generative AI</p>
            </div>
          </div>
          <p className="text-green-100 text-lg max-w-2xl leading-relaxed mb-8">
            Upload a food image or search for any food to get instant nutritional analysis,
            ingredient information, allergen data, and AI-powered explanations — all backed by
            verified data sources.
          </p>
          <div className="flex flex-wrap gap-4">
            <button
              onClick={() => navigate('/analyze')}
              className="flex items-center gap-2 bg-[#52b788] hover:bg-[#40916c] text-white font-semibold px-6 py-3 rounded-xl transition-all shadow-lg shadow-green-900/20"
            >
              <Camera className="w-5 h-5" />
              Analyze Food Image
            </button>
            <button
              onClick={() => navigate('/nutrition')}
              className="flex items-center gap-2 bg-white/10 hover:bg-white/20 text-white font-semibold px-6 py-3 rounded-xl transition-all border border-white/20"
            >
              <Search className="w-5 h-5" />
              Search Food
            </button>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        {stats.map(({ icon: Icon, label, value, sub }) => (
          <div key={label} className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5 text-center">
            <div className="w-10 h-10 rounded-xl bg-[#e8f4ed] flex items-center justify-center mx-auto mb-3">
              <Icon className="w-5 h-5 text-[#2d6a4f]" />
            </div>
            <p className="text-2xl font-bold text-gray-900">{value}</p>
            <p className="text-xs text-gray-500 mt-0.5">{label}</p>
            <p className="text-xs text-[#2d6a4f] font-medium">{sub}</p>
          </div>
        ))}
      </div>

      {/* Features */}
      <h2 className="text-xl font-bold text-gray-900 mb-4">Features</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {features.map(({ icon: Icon, title, description, color, bg, path }) => (
          <button
            key={title}
            onClick={() => navigate(path)}
            className="text-left bg-white rounded-2xl border border-gray-100 shadow-sm p-6 hover:shadow-md hover:border-[#b7e4c7] transition-all group"
          >
            <div className={`w-12 h-12 rounded-xl ${bg} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}>
              <div className={`w-7 h-7 rounded-lg bg-gradient-to-br ${color} flex items-center justify-center`}>
                <Icon className="w-4 h-4 text-white" />
              </div>
            </div>
            <h3 className="font-bold text-gray-900 mb-2">{title}</h3>
            <p className="text-sm text-gray-500 leading-relaxed">{description}</p>
          </button>
        ))}
      </div>

      {/* Disclaimer */}
      <div className="mt-8 bg-amber-50 border border-amber-200 rounded-2xl p-4">
        <p className="text-xs text-amber-700">
          <strong>Academic Project Notice:</strong> NutriGuide AI is a Computer Science academic project
          built at Siddaganga Institute of Technology. Nutritional data comes from USDA FoodData Central
          and Open Food Facts. This application does not provide medical or dietary advice.
          Always consult a qualified professional for health-related decisions.
        </p>
      </div>
    </div>
  )
}
