import { useNavigate } from 'react-router-dom'
import { Camera, Search, BarChart3, ShieldAlert, MessageSquare, GitCompare, Leaf } from 'lucide-react'

const features = [
  {
    icon: Camera,
    title: 'Food Recognition',
    description: 'Upload a food photo and our MobileNetV3 AI identifies it. Gemma 3 vision fallback supports any food beyond trained categories.',
    path: '/analyze',
  },
  {
    icon: BarChart3,
    title: 'Nutrition Analysis',
    description: 'Get detailed nutritional data from USDA FoodData Central — calories, protein, carbs, and more.',
    path: '/nutrition',
  },
  {
    icon: ShieldAlert,
    title: 'Allergen Awareness',
    description: 'Search packaged products for ingredient lists and declared allergen information via Open Food Facts.',
    path: '/ingredients',
  },
  {
    icon: MessageSquare,
    title: 'AI Nutrition Assistant',
    description: 'Ask questions about any food. Our Gemma 3-powered assistant uses RAG to give evidence-grounded answers.',
    path: '/assistant',
  },
  {
    icon: GitCompare,
    title: 'Food Comparison',
    description: 'Compare two foods side-by-side on a per-100g basis with AI-generated nutritional insights.',
    path: '/compare',
  },
]

const stats = [
  { label: 'Food Categories', value: '101+', sub: 'AI-recognized' },
  { label: 'Data Source', value: 'USDA', sub: 'FoodData Central' },
  { label: 'AI Model', value: 'Gemma 3 4B', sub: '+ RAG Pipeline' },
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
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
        {stats.map(({ label, value, sub }) => (
          <div
            key={label}
            className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 text-center flex flex-col items-center justify-center hover:border-[#52b788]/30 transition-all"
          >
            <p className="text-3xl font-bold text-gray-900 tracking-tight">{value}</p>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mt-1">{label}</p>
            <span className="inline-block mt-2 px-2.5 py-0.5 bg-[#e8f4ed] text-[#2d6a4f] text-xs font-semibold rounded-full">
              {sub}
            </span>
          </div>
        ))}
      </div>

      {/* Features */}
      <h2 className="text-xl font-bold text-gray-900 mb-4">Features</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {features.map(({ icon: Icon, title, description, path }) => (
          <button
            key={title}
            onClick={() => navigate(path)}
            className="text-left bg-white rounded-2xl border border-gray-100 shadow-sm p-6 hover:shadow-md hover:border-[#52b788]/50 transition-all group flex flex-col justify-between"
          >
            <div>
              <div className="w-11 h-11 rounded-xl bg-[#e8f4ed] text-[#2d6a4f] flex items-center justify-center mb-4 group-hover:bg-[#2d6a4f] group-hover:text-white transition-colors duration-200">
                <Icon className="w-5 h-5 transition-colors" />
              </div>
              <h3 className="font-bold text-gray-900 mb-2 group-hover:text-[#2d6a4f] transition-colors">{title}</h3>
              <p className="text-sm text-gray-500 leading-relaxed">{description}</p>
            </div>
            <div className="mt-5 pt-3 border-t border-gray-50 flex items-center text-xs font-semibold text-[#2d6a4f]">
              <span className="group-hover:translate-x-0.5 transition-transform">Explore feature &rarr;</span>
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}
