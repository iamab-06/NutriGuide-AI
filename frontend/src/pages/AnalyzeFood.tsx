import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Camera, Upload, AlertTriangle, CheckCircle, ChevronDown, ChevronUp } from 'lucide-react'
import { analyzeImage } from '../services/api'
import type { AnalyzeImageResponse } from '../types'
import NutritionCard from '../components/NutritionCard'
import ConfidenceBadge from '../components/ConfidenceBadge'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorMessage from '../components/ErrorMessage'

export default function AnalyzeFood() {
  const [result, setResult] = useState<AnalyzeImageResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [showAlts, setShowAlts] = useState(false)

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0]
    if (!file) return

    // Validate
    const allowed = ['image/jpeg', 'image/png', 'image/webp']
    if (!allowed.includes(file.type)) {
      setError('Please upload a JPEG, PNG, or WebP image.')
      return
    }
    if (file.size > 10 * 1024 * 1024) {
      setError('Image must be smaller than 10 MB.')
      return
    }

    setPreview(URL.createObjectURL(file))
    setError(null)
    setResult(null)
    setLoading(true)

    try {
      const data = await analyzeImage(file)
      setResult(data)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Analysis failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/*': ['.jpg', '.jpeg', '.png', '.webp'] },
    maxFiles: 1,
    disabled: loading,
  })

  const resetAll = () => {
    setResult(null)
    setPreview(null)
    setError(null)
    setShowAlts(false)
  }

  return (
    <div className="p-6 lg:p-8 max-w-4xl mx-auto">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Analyze Food Image</h2>
        <p className="text-gray-500 text-sm mt-1">
          Upload a photo of food to identify it and retrieve its nutritional information.
          Supports 20 food categories.
        </p>
      </div>

      {/* Dropzone */}
      {!result && (
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all mb-6 ${
            isDragActive
              ? 'border-[#52b788] bg-[#e8f4ed]'
              : 'border-gray-200 bg-white hover:border-[#52b788] hover:bg-[#f8fdf9]'
          } ${loading ? 'opacity-60 cursor-not-allowed' : ''}`}
        >
          <input {...getInputProps()} />
          <div className="flex flex-col items-center gap-4">
            {preview ? (
              <img
                src={preview}
                alt="Food preview"
                className="w-48 h-48 object-cover rounded-xl shadow-md"
              />
            ) : (
              <div className="w-20 h-20 rounded-2xl bg-[#e8f4ed] flex items-center justify-center">
                {isDragActive ? <Upload className="w-10 h-10 text-[#2d6a4f]" /> : <Camera className="w-10 h-10 text-[#2d6a4f]" />}
              </div>
            )}
            <div>
              <p className="font-semibold text-gray-700">
                {isDragActive ? 'Drop the image here' : preview ? 'Drop a new image to re-analyze' : 'Drag & drop your food image'}
              </p>
              <p className="text-sm text-gray-400 mt-1">or click to browse &bull; JPEG, PNG, WebP &bull; max 10 MB</p>
            </div>
          </div>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-8">
          <LoadingSpinner message="Analyzing image... Classifying food and retrieving nutrition data..." size="lg" />
        </div>
      )}

      {/* Error */}
      {error && <ErrorMessage message={error} onRetry={resetAll} />}

      {/* Results */}
      {result && !loading && (
        <div className="space-y-6">
          {/* Image + Classification */}
          <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
            <div className="flex flex-col sm:flex-row">
              {preview && (
                <img
                  src={preview}
                  alt="Analyzed food"
                  className="sm:w-64 h-48 sm:h-auto object-cover flex-shrink-0"
                />
              )}
              <div className="p-6 flex-1">
                <div className="flex items-start justify-between gap-4 mb-3">
                  <div>
                    <h3 className="text-xl font-bold text-gray-900">
                      {result.classification.display_name}
                    </h3>
                    <p className="text-sm text-gray-500 mt-0.5">
                      {result.classification.model_version}
                    </p>
                  </div>
                  <ConfidenceBadge
                    confidence={result.classification.confidence}
                    isConfident={result.classification.is_confident}
                  />
                </div>

                {!result.classification.is_confident && (
                  <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-3 mb-4 flex items-start gap-2">
                    <AlertTriangle className="w-4 h-4 text-yellow-600 flex-shrink-0 mt-0.5" />
                    <p className="text-sm text-yellow-700">{result.message}</p>
                  </div>
                )}

                {result.classification.is_confident && result.message && (
                  <div className="bg-green-50 border border-green-200 rounded-xl p-3 mb-4 flex items-start gap-2">
                    <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0 mt-0.5" />
                    <p className="text-sm text-green-700">{result.message || 'Food identified successfully.'}</p>
                  </div>
                )}

                {/* Top predictions toggle */}
                {result.classification.top_predictions.length > 1 && (
                  <div>
                    <button
                      onClick={() => setShowAlts(!showAlts)}
                      className="flex items-center gap-1 text-sm text-[#2d6a4f] hover:text-[#1a3d2b] font-medium transition-colors"
                    >
                      {showAlts ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                      {showAlts ? 'Hide' : 'Show'} alternative predictions
                    </button>
                    {showAlts && (
                      <div className="mt-3 space-y-2">
                        {result.classification.top_predictions.slice(1).map((pred) => (
                          <div key={pred.class} className="flex items-center gap-3">
                            <span className="text-sm text-gray-600 flex-1">{pred.display_name}</span>
                            <div className="flex-1 bg-gray-100 rounded-full h-2">
                              <div
                                className="bg-[#52b788] h-2 rounded-full transition-all"
                                style={{ width: `${pred.confidence * 100}%` }}
                              />
                            </div>
                            <span className="text-xs text-gray-500 w-12 text-right">{pred.confidence_pct}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Nutrition */}
          {result.nutrition && <NutritionCard data={result.nutrition} />}
          {!result.nutrition && result.classification.is_confident && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-2xl p-5">
              <p className="text-yellow-800 font-medium">Nutrition data not available</p>
              <p className="text-sm text-yellow-700 mt-1">Could not retrieve nutritional information from USDA for this food.</p>
            </div>
          )}

          <button
            onClick={resetAll}
            className="w-full py-3 rounded-xl border-2 border-[#2d6a4f] text-[#2d6a4f] font-semibold hover:bg-[#e8f4ed] transition-all"
          >
            Analyze Another Image
          </button>
        </div>
      )}

      {/* Supported categories */}
      <div className="mt-8 bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
        <h4 className="font-semibold text-gray-700 mb-3">Supported Food Categories (20)</h4>
        <div className="flex flex-wrap gap-2">
          {['Apple Pie','Caesar Salad','Chicken Curry','Chocolate Cake','Donuts',
            'French Fries','Fried Rice','Hamburger','Hot Dog','Ice Cream',
            'Omelette','Pancakes','Pizza','Ramen','Samosa',
            'Spaghetti Bolognese','Spring Rolls','Steak','Sushi','Waffles'].map(cat => (
            <span key={cat} className="px-3 py-1 bg-[#e8f4ed] text-[#2d6a4f] text-xs font-medium rounded-full">
              {cat}
            </span>
          ))}
        </div>
      </div>
    </div>
  )
}
