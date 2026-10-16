import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import AnalyzeFood from './pages/AnalyzeFood'
import NutritionInfo from './pages/NutritionInfo'
import IngredientsAllergens from './pages/IngredientsAllergens'
import AIAssistant from './pages/AIAssistant'
import CompareFoods from './pages/CompareFoods'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="analyze" element={<AnalyzeFood />} />
          <Route path="nutrition" element={<NutritionInfo />} />
          <Route path="ingredients" element={<IngredientsAllergens />} />
          <Route path="assistant" element={<AIAssistant />} />
          <Route path="compare" element={<CompareFoods />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
