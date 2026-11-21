import { Outlet, NavLink, useLocation } from 'react-router-dom'
import {
  Leaf, Camera, BarChart3, ShieldAlert, MessageSquare,
  GitCompare, Menu, X, Activity, ShieldCheck
} from 'lucide-react'
import { useState, useEffect } from 'react'

const navItems = [
  { path: '/', label: 'Dashboard', icon: Activity },
  { path: '/analyze', label: 'Analyze Food', icon: Camera },
  { path: '/nutrition', label: 'Nutrition Info', icon: BarChart3 },
  { path: '/ingredients', label: 'Ingredients & Allergens', icon: ShieldAlert },
  { path: '/assistant', label: 'AI Assistant', icon: MessageSquare },
  { path: '/compare', label: 'Compare Foods', icon: GitCompare },
]

const pageMeta: Record<string, { title: string; subtitle: string }> = {
  '/': { title: 'Dashboard', subtitle: 'Overview of nutritional AI models and computer vision metrics' },
  '/analyze': { title: 'Analyze Food', subtitle: 'Identify foods, segment Indian thali plates, and evaluate clinical health safety' },
  '/nutrition': { title: 'Nutrition Info', subtitle: 'Search USDA FoodData Central for comprehensive macro and micronutrients' },
  '/ingredients': { title: 'Ingredients & Allergens', subtitle: 'Package ingredient breakdown and allergen safety via Open Food Facts' },
  '/assistant': { title: 'AI Assistant', subtitle: 'Evidence-grounded conversational dietary advisor powered by Gemma 3 & RAG' },
  '/compare': { title: 'Compare Foods', subtitle: 'Side-by-side nutritional comparison and AI-generated dietary evaluation' },
}

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const location = useLocation()
  const currentMeta = pageMeta[location.pathname] || { title: 'NutriGuide AI', subtitle: 'Intelligent nutritional analysis & food safety' }

  const [activeConditionCount, setActiveConditionCount] = useState<number>(() => {
    try {
      const saved = localStorage.getItem('nutriguide_active_conditions')
      return saved ? JSON.parse(saved).length : 2
    } catch {
      return 2
    }
  })

  useEffect(() => {
    const updateCount = () => {
      try {
        const saved = localStorage.getItem('nutriguide_active_conditions')
        setActiveConditionCount(saved ? JSON.parse(saved).length : 2)
      } catch {
        setActiveConditionCount(2)
      }
    }

    window.addEventListener('storage', updateCount)
    window.addEventListener('nutriguide_conditions_changed', updateCount)
    return () => {
      window.removeEventListener('storage', updateCount)
      window.removeEventListener('nutriguide_conditions_changed', updateCount)
    }
  }, [])

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-20 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed lg:static inset-y-0 left-0 z-30 w-64 bg-[#0d2818] flex flex-col transition-transform duration-300
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}`}
      >
        {/* Logo */}
        <div className="flex items-center gap-3 px-6 py-6 border-b border-white/10">
          <div className="w-10 h-10 rounded-xl bg-[#52b788] flex items-center justify-center flex-shrink-0">
            <Leaf className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-white font-bold text-lg leading-tight">NutriGuide</h1>
            <p className="text-[#52b788] text-xs font-medium">AI</p>
          </div>
          <button
            className="ml-auto lg:hidden text-white/60 hover:text-white"
            onClick={() => setSidebarOpen(false)}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-4 py-6 space-y-1 overflow-y-auto">
          {navItems.map(({ path, label, icon: Icon }) => (
            <NavLink
              key={path}
              to={path}
              end={path === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400/70 ${
                  isActive
                    ? 'bg-[#52b788] text-white shadow-lg shadow-[#52b788]/20'
                    : 'text-white/60 hover:text-white hover:bg-white/5'
                }`
              }
              onClick={() => setSidebarOpen(false)}
            >
              <Icon className="w-5 h-5 flex-shrink-0" />
              {label}
            </NavLink>
          ))}
        </nav>

      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top bar */}
        <header className="h-16 bg-white border-b border-gray-100 flex items-center justify-between px-4 sm:px-6 lg:px-8 gap-4 flex-shrink-0">
          <div className="flex items-center gap-3 min-w-0">
            <button
              className="lg:hidden p-1.5 -ml-1 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
              onClick={() => setSidebarOpen(true)}
              aria-label="Open menu"
            >
              <Menu className="w-5 h-5" />
            </button>
            <div className="min-w-0">
              <h2 className="text-base sm:text-lg font-bold text-gray-900 truncate leading-tight">
                {currentMeta.title}
              </h2>
              <p className="text-xs text-gray-500 truncate hidden sm:block">
                {currentMeta.subtitle}
              </p>
            </div>
          </div>
          {location.pathname === '/analyze' && (
            <div className="flex items-center gap-2 flex-shrink-0">
              <div className="hidden sm:flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200/80">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                <span>{activeConditionCount} Active Health {activeConditionCount === 1 ? 'Filter' : 'Filters'}</span>
              </div>
              <div className="flex sm:hidden items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200/80">
                <ShieldCheck className="w-3 h-3 text-emerald-600" />
                <span>{activeConditionCount}</span>
              </div>
            </div>
          )}
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
