import { useState } from 'react'
import { Search, ShieldAlert, AlertTriangle, Loader2, Package } from 'lucide-react'
import { searchProducts, getProductByBarcode } from '../services/api'
import type { ProductInfo } from '../types'
import ErrorMessage from '../components/ErrorMessage'

function AllergenBadge({ tag }: { tag: string }) {
  const name = tag.replace('en:', '').replace(/-/g, ' ')
  return (
    <span className="px-2 py-1 bg-red-100 text-red-700 text-xs font-semibold rounded-full capitalize">
      {name}
    </span>
  )
}

function ProductCard({ product }: { product: ProductInfo }) {
  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
      <div className="flex gap-4 p-6">
        {product.image_url && (
          <img src={product.image_url} alt={product.product_name || 'Product'} className="w-24 h-24 object-contain rounded-xl flex-shrink-0 bg-gray-50" />
        )}
        <div className="flex-1 min-w-0">
          <h3 className="font-bold text-gray-900 text-lg truncate">{product.product_name || 'Unknown Product'}</h3>
          {product.brands && <p className="text-sm text-gray-500">{product.brands}</p>}
          {product.barcode && <p className="text-xs text-gray-400 mt-1">Barcode: {product.barcode}</p>}
        </div>
      </div>

      {/* Allergens */}
      <div className="px-6 pb-4">
        <div className="flex items-center gap-2 mb-3">
          <ShieldAlert className="w-4 h-4 text-red-500" />
          <h4 className="font-semibold text-gray-800">Allergen Information</h4>
        </div>
        {product.allergens_tags.length > 0 ? (
          <div className="flex flex-wrap gap-2 mb-2">
            {product.allergens_tags.map(tag => <AllergenBadge key={tag} tag={tag} />)}
          </div>
        ) : (
          <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-3 flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 text-yellow-600 flex-shrink-0 mt-0.5" />
            <p className="text-sm text-yellow-700">
              No allergens declared in database. <strong>This does NOT confirm the product is allergen-free.</strong>
              Always check the physical product label.
            </p>
          </div>
        )}
        {product.allergens && (
          <p className="text-sm text-gray-600 mt-2"><strong>Declared:</strong> {product.allergens}</p>
        )}
      </div>

      {/* Ingredients */}
      {product.ingredients_text && (
        <div className="px-6 pb-4">
          <h4 className="font-semibold text-gray-800 mb-2">Ingredients</h4>
          <p className="text-sm text-gray-600 leading-relaxed bg-gray-50 rounded-xl p-3">
            {product.ingredients_text}
          </p>
        </div>
      )}

      {/* Missing data warning */}
      {product.missing_fields.length > 0 && (
        <div className="mx-6 mb-4 bg-orange-50 border border-orange-200 rounded-xl p-3 flex items-start gap-2">
          <AlertTriangle className="w-4 h-4 text-orange-500 flex-shrink-0 mt-0.5" />
          <p className="text-sm text-orange-700">
            Missing from database: {product.missing_fields.join(', ')}. Check the physical product.
          </p>
        </div>
      )}

      <div className="px-6 pb-4">
        <p className="text-xs text-gray-400">Source: {product.source}</p>
      </div>
    </div>
  )
}

export default function IngredientsAllergens() {
  const [query, setQuery] = useState('')
  const [barcode, setBarcode] = useState('')
  const [products, setProducts] = useState<ProductInfo[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [searched, setSearched] = useState(false)
  const [tab, setTab] = useState<'name' | 'barcode'>('name')

  const handleSearchByName = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return
    setLoading(true)
    setError(null)
    setProducts([])
    setSearched(true)
    try {
      const results = await searchProducts(query.trim(), 5)
      if (results.length === 0) setError(`No products found for "${query}".`)
      else setProducts(results)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Search failed.')
    } finally {
      setLoading(false)
    }
  }

  const handleSearchByBarcode = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!barcode.trim()) return
    setLoading(true)
    setError(null)
    setProducts([])
    setSearched(true)
    try {
      const result = await getProductByBarcode(barcode.trim())
      setProducts([result])
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Barcode lookup failed.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-6 lg:p-8 max-w-4xl mx-auto">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Ingredients & Allergens</h2>
        <p className="text-gray-500 text-sm mt-1">
          Search packaged products for ingredient lists and declared allergen information from Open Food Facts.
        </p>
      </div>

      <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4 mb-6 flex items-start gap-3">
        <ShieldAlert className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
        <p className="text-sm text-amber-700">
          <strong>Important:</strong> Allergen information is sourced from Open Food Facts community database.
          Absence of allergen data does NOT confirm a product is allergen-free. Always verify with the physical product label.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6">
        {(['name', 'barcode'] as const).map((t) => (
          <button
            key={t}
            onClick={() => { setTab(t); setProducts([]); setError(null); setSearched(false) }}
            className={`px-5 py-2.5 rounded-xl font-medium text-sm transition-all ${
              tab === t ? 'bg-[#2d6a4f] text-white shadow-sm' : 'bg-white text-gray-600 hover:bg-gray-50 border border-gray-200'
            }`}
          >
            {t === 'name' ? 'Search by Name' : 'Search by Barcode'}
          </button>
        ))}
      </div>

      {/* Search form */}
      {tab === 'name' ? (
        <form onSubmit={handleSearchByName} className="flex gap-3 mb-6">
          <div className="flex-1 relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input type="text" value={query} onChange={e => setQuery(e.target.value)}
              placeholder="Product name (e.g., Nutella, Oreo, Lay's)"
              className="w-full pl-12 pr-4 py-3 rounded-xl border border-gray-200 bg-white focus:outline-none focus:ring-2 focus:ring-[#52b788] focus:border-transparent"
            />
          </div>
          <button type="submit" disabled={loading || !query.trim()}
            className="px-6 py-3 bg-[#2d6a4f] hover:bg-[#1a3d2b] disabled:opacity-50 text-white font-semibold rounded-xl flex items-center gap-2">
            {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Search className="w-5 h-5" />}
            Search
          </button>
        </form>
      ) : (
        <form onSubmit={handleSearchByBarcode} className="flex gap-3 mb-6">
          <div className="flex-1 relative">
            <Package className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input type="text" value={barcode} onChange={e => setBarcode(e.target.value)}
              placeholder="Enter product barcode (e.g., 3017620422003)"
              className="w-full pl-12 pr-4 py-3 rounded-xl border border-gray-200 bg-white focus:outline-none focus:ring-2 focus:ring-[#52b788] focus:border-transparent"
            />
          </div>
          <button type="submit" disabled={loading || !barcode.trim()}
            className="px-6 py-3 bg-[#2d6a4f] hover:bg-[#1a3d2b] disabled:opacity-50 text-white font-semibold rounded-xl flex items-center gap-2">
            {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Search className="w-5 h-5" />}
            Lookup
          </button>
        </form>
      )}

      {error && <ErrorMessage message={error} />}

      {loading && (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-8 text-center">
          <Loader2 className="w-8 h-8 text-[#2d6a4f] animate-spin mx-auto mb-3" />
          <p className="text-gray-500">Searching Open Food Facts...</p>
        </div>
      )}

      <div className="space-y-4">
        {products.map((p, i) => <ProductCard key={p.barcode || i} product={p} />)}
      </div>

      {!searched && (
        <div className="bg-[#e8f4ed] rounded-2xl p-8 text-center">
          <ShieldAlert className="w-12 h-12 text-[#2d6a4f] mx-auto mb-4" />
          <p className="text-[#2d6a4f] font-semibold">Search for a packaged product</p>
          <p className="text-sm text-[#40916c] mt-2">Try: Nutella, Oreo, Pringles, or enter a barcode</p>
        </div>
      )}
    </div>
  )
}
