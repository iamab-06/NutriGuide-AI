import { Outlet, NavLink } from 'react-router-dom'
import {
  Leaf, Camera, BarChart3, ShieldAlert, MessageSquare,
  GitCompare, Menu, X, Activity
} from 'lucide-react'
import { useState } from 'react'

const navItems = [
  { path: '/', label: 'Dashboard', icon: Activity },
  { path: '/analyze', label: 'Analyze Food', icon: Camera },
  { path: '/nutrition', label: 'Nutrition Info', icon: BarChart3 },
  { path: '/ingredients', label: 'Ingredients & Allergens', icon: ShieldAlert },
  { path: '/assistant', label: 'AI Assistant', icon: MessageSquare },
  { path: '/compare', label: 'Compare Foods', icon: GitCompare },
]

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)

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
                `flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-150 ${
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
        <header className="h-16 bg-white border-b border-gray-100 flex items-center px-6 gap-4 flex-shrink-0">
          <button
            className="lg:hidden text-gray-500 hover:text-gray-700"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu className="w-6 h-6" />
          </button>
          <div className="flex-1" />
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
