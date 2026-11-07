import { useState, useCallback, useEffect } from 'react'
import { useDropzone } from 'react-dropzone'
import {
  Camera,
  Upload,
  AlertTriangle,
  CheckCircle,
  ChevronDown,
  ChevronUp,
  Sparkles,
  Check,
  ShieldAlert,
  Ban,
  UtensilsCrossed,
  Layers,
} from 'lucide-react'
import {
  analyzeImage,
  analyzeMealPlate,
  getNutrition,
  getCategories,
  evaluateHealthSafety,
} from '../services/api'
import type { AnalyzeImageResponse, MealPlateAnalysis } from '../types'
import NutritionCard from '../components/NutritionCard'
import ConfidenceBadge from '../components/ConfidenceBadge'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorMessage from '../components/ErrorMessage'
import HealthProfileSelector from '../components/HealthProfileSelector'
import HealthSafetyCard from '../components/HealthSafetyCard'
import MealPlateCard from '../components/MealPlateCard'

export default function AnalyzeFood() {
  const [result, setResult] = useState<AnalyzeImageResponse | null>(null)
  const [plateResult, setPlateResult] = useState<MealPlateAnalysis | null>(null)
  const [currentFile, setCurrentFile] = useState<File | null>(null)
  const [scanMode, setScanMode] = useState<'single' | 'plate'>('single')
  const [selectedConditions, setSelectedConditions] = useState<string[]>(() => {
    try {
      const saved = localStorage.getItem('nutriguide_active_conditions')
      return saved ? JSON.parse(saved) : ['diabetes', 'hypertension']
    } catch {
      return ['diabetes', 'hypertension']
    }
  })

  const [loading, setLoading] = useState(false)
  const [loadingNutrition, setLoadingNutrition] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [showAlts, setShowAlts] = useState(false)
  const [allCategories, setAllCategories] = useState<string[]>([
    'Apple Pie','Caesar Salad','Chicken Curry','Chocolate Cake','Donuts',
    'French Fries','Fried Rice','Hamburger','Hot Dog','Ice Cream',
    'Omelette','Pancakes','Pizza','Ramen','Samosa',
    'Spaghetti Bolognese','Spring Rolls','Steak','Sushi','Waffles'
  ])
  const [categoryCount, setCategoryCount] = useState(20)

  useEffect(() => {
    getCategories()
      .then((data: any) => {
        if (data?.all_display_names) {
          const names = Object.values(data.all_display_names) as string[]
          setAllCategories(names)
          setCategoryCount(data.total_food101_count ?? names.length)
        }
      })
      .catch(() => {
        /* keep defaults */
      })
  }, [])

  const handleConditionsChange = (nextConditions: string[]) => {
    setSelectedConditions(nextConditions)
    if (result && result.nutrition) {
      evaluateHealthSafety(
        result.classification.display_name,
        result.classification.predicted_class,
        result.nutrition,
        nextConditions,
        100.0
      )
        .then((safety) => {
          setResult((prev) => (prev ? { ...prev, health_safety: safety } : null))
        })
        .catch(() => {
          // ignore
        })
    }
  }

  const performAnalysis = async (file: File, mode: 'single' | 'plate', conditions: string[]) => {
    setLoading(true)
    setError(null)
    try {
      if (mode === 'plate') {
        setResult(null)
        const pData = await analyzeMealPlate(file, conditions)
        setPlateResult(pData)
      } else {
        setPlateResult(null)
        const sData = await analyzeImage(file, conditions)
        setResult(sData)
        setShowAlts(!sData.classification.is_confident)
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Analysis failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      const file = acceptedFiles[0]
      if (!file) return

      const allowed = ['image/jpeg', 'image/png', 'image/webp']
      if (!allowed.includes(file.type)) {
        setError('Please upload a JPEG, PNG, or WebP image.')
        return
      }
      if (file.size > 10 * 1024 * 1024) {
        setError('Image must be smaller than 10 MB.')
        return
      }

      setCurrentFile(file)
      setPreview(URL.createObjectURL(file))
      await performAnalysis(file, scanMode, selectedConditions)
    },
    [scanMode, selectedConditions]
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/*': ['.jpg', '.jpeg', '.png', '.webp'] },
    maxFiles: 1,
    disabled: loading,
  })

  const resetAll = () => {
    setResult(null)
    setPlateResult(null)
    setCurrentFile(null)
    setPreview(null)
    setError(null)
    setShowAlts(false)
  }

  const handleSelectAlternative = async (displayName: string, categoryKey: string) => {
    setLoadingNutrition(true)
    try {
      const nut = await getNutrition(displayName, categoryKey)
      let safetyReport = null
      if (selectedConditions.length > 0) {
        try {
          safetyReport = await evaluateHealthSafety(
            displayName,
            categoryKey,
            nut,
            selectedConditions,
            100.0
          )
        } catch {
          // ignore
        }
      }
      setResult((prev) =>
        prev
          ? {
              ...prev,
              classification: {
                ...prev.classification,
                display_name: displayName,
                predicted_class: categoryKey,
                is_confident: true,
              },
              nutrition: nut,
              health_safety: safetyReport,
              message: `Food confirmed as ${displayName}. Nutrition data retrieved.`,
            }
          : null
      )
    } catch {
      setError(`Failed to retrieve nutrition for ${displayName}.`)
    } finally {
      setLoadingNutrition(false)
    }
  }

  const switchModeAndReanalyze = (newMode: 'single' | 'plate') => {
    setScanMode(newMode)
    if (currentFile) {
      performAnalysis(currentFile, newMode, selectedConditions)
    }
  }

  return (
    <div className="p-6 lg:p-8 max-w-4xl mx-auto">
      {/* Header */}
      {/* Feature 2: Health Profile Condition Selector */}
      <HealthProfileSelector
        selectedConditions={selectedConditions}
        onChange={handleConditionsChange}
      />

      {/* Mode Selector Tabs */}
      <div className="flex bg-gray-100 p-1 rounded-2xl mb-6 shadow-2xs max-w-md">
        <button
          type="button"
          onClick={() => switchModeAndReanalyze('single')}
          className={`flex-1 py-2 px-3 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-2 ${
            scanMode === 'single'
              ? 'bg-white text-[#2d6a4f] shadow-xs'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          <Layers className="w-4 h-4" />
          <span>Single Dish / Item</span>
        </button>
        <button
          type="button"
          onClick={() => switchModeAndReanalyze('plate')}
          className={`flex-1 py-2 px-3 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-2 ${
            scanMode === 'plate'
              ? 'bg-[#2d6a4f] text-white shadow-xs'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          <UtensilsCrossed className="w-4 h-4" />
          <span>Meal Plate / Thali Scanner</span>
        </button>
      </div>

      {/* Dropzone */}
      {!result && !plateResult && (
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
                {isDragActive ? (
                  <Upload className="w-10 h-10 text-[#2d6a4f]" />
                ) : (
                  <Camera className="w-10 h-10 text-[#2d6a4f]" />
                )}
              </div>
            )}
            <div>
              <p className="font-semibold text-gray-700">
                {isDragActive
                  ? 'Drop the image here'
                  : preview
                  ? 'Drop a new image to re-analyze'
                  : scanMode === 'plate'
                  ? 'Drag & drop your Indian thali or multi-item plate'
                  : 'Drag & drop your food image'}
              </p>
              <p className="text-sm text-gray-400 mt-1">
                {scanMode === 'plate'
                  ? 'Gemma 3 Vision will decompose each item (Rice, Sambar, Palya, Roti, Curd)'
                  : 'or click to browse &bull; JPEG, PNG, WebP &bull; max 10 MB'}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-8 mb-6">
          <LoadingSpinner
            message={
              scanMode === 'plate'
                ? 'Decomposing meal plate components with Gemma 3 Vision and retrieving verified ICMR-NIN & USDA nutritional macros...'
                : 'Analyzing image... Classifying food and screening against health profile...'
            }
            size="lg"
          />
        </div>
      )}

      {/* Error */}
      {error && <ErrorMessage message={error} onRetry={resetAll} />}

      {/* Feature 1: Multi-Item Meal Plate / Thali Result */}
      {plateResult && !loading && (
        <div className="space-y-6">
          {preview && (
            <div className="bg-white rounded-2xl border border-gray-100 p-4 shadow-xs flex items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <img src={preview} alt="Plate preview" className="w-16 h-16 rounded-xl object-cover" />
                <div>
                  <h4 className="font-bold text-gray-900 text-sm">{plateResult.meal_title}</h4>
                  <p className="text-xs text-gray-500">{plateResult.items_detected_count} distinct dishes segmented</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => switchModeAndReanalyze('single')}
                className="text-xs font-semibold px-3 py-1.5 rounded-lg border border-gray-200 text-gray-700 hover:bg-gray-50 transition-colors"
              >
                Switch to Single Item View
              </button>
            </div>
          )}

          <MealPlateCard analysis={plateResult} />

          <button
            onClick={resetAll}
            className="w-full py-3 rounded-xl border-2 border-[#2d6a4f] text-[#2d6a4f] font-semibold hover:bg-[#e8f4ed] transition-all"
          >
            Analyze Another Meal Plate
          </button>
        </div>
      )}

      {/* Single Item Analysis Result */}
      {result && !loading && !plateResult && (
        <div className="space-y-6">
          {/* Option to switch to Plate decomposition directly */}
          {currentFile && (
            <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-3 flex items-center justify-between text-xs text-emerald-800">
              <div className="flex items-center gap-2">
                <UtensilsCrossed className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                <span>Does this plate have multiple items (e.g. Rice + Sambar + Palya)?</span>
              </div>
              <button
                type="button"
                onClick={() => switchModeAndReanalyze('plate')}
                className="font-bold text-xs bg-[#2d6a4f] hover:bg-[#1a3d2b] text-white px-3 py-1 rounded-lg transition-all"
              >
                Decompose Complete Plate
              </button>
            </div>
          )}

          {/* Image + Classification Card */}
          <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
            <div className="flex flex-col sm:flex-row">
              {preview && (
                <img
                  src={preview}
                  alt="Analyzed food"
                  className="sm:w-64 h-48 sm:h-auto object-cover flex-shrink-0"
                />
              )}

              {/* Details */}
              {(() => {
                const isNonFood = result.is_food === false || result.gemini_fallback?.is_food === false
                return (
                  <div className="p-6 flex-1 flex flex-col justify-between">
                    <div>
                      <div className="flex items-start justify-between gap-4 mb-3">
                        <div>
                          <h3
                            className={`text-xl font-bold ${
                              isNonFood ? 'text-red-900 flex items-center gap-2' : 'text-gray-900'
                            }`}
                          >
                            {isNonFood && <ShieldAlert className="w-5 h-5 text-red-600 flex-shrink-0" />}
                            {isNonFood
                              ? result.gemini_fallback?.suggested_food &&
                                result.gemini_fallback.suggested_food.toLowerCase() !== 'unknown'
                                ? result.gemini_fallback.suggested_food
                                : 'Non-Food Item Detected'
                              : result.classification.display_name}
                          </h3>
                          <p className={`text-sm mt-0.5 ${isNonFood ? 'text-red-600 font-medium' : 'text-gray-500'}`}>
                            {isNonFood ? 'Restricted by Food Safety Guardrail' : result.classification.model_version}
                          </p>
                        </div>
                        {isNonFood ? (
                          <span className="px-2.5 py-1 bg-red-100 text-red-700 text-xs font-bold rounded-full uppercase tracking-wider">
                            Not Food
                          </span>
                        ) : (
                          <ConfidenceBadge
                            confidence={result.classification.confidence}
                            isConfident={result.classification.is_confident}
                          />
                        )}
                      </div>

                      {isNonFood ? (
                        <div className="space-y-4 mb-4">
                          <div className="bg-red-50 border border-red-200 rounded-xl p-4 shadow-2xs">
                            <div className="flex items-center gap-2 mb-2">
                              <ShieldAlert className="w-4 h-4 text-red-600" />
                              <span className="text-xs font-bold text-red-800 uppercase tracking-wider">
                                Gemma 3 Multimodal Guardrail
                              </span>
                              <span className="text-xs bg-red-100 text-red-800 font-bold px-2 py-0.5 rounded-full ml-auto">
                                Rejected
                              </span>
                            </div>
                            <p className="text-sm font-bold text-red-950 mb-1">
                              {result.gemini_fallback?.suggested_food &&
                              result.gemini_fallback.suggested_food.toLowerCase() !== 'unknown'
                                ? `Identified Subject: ${result.gemini_fallback.suggested_food}`
                                : 'No Edible Food Detected'}
                            </p>
                            <p className="text-xs text-red-800 leading-relaxed">
                              {result.gemini_fallback?.explanation || result.message}
                            </p>
                            <div className="mt-3 p-3 bg-white/90 border border-red-100 rounded-lg text-xs text-red-800">
                              <p className="font-semibold mb-0.5">Nutritional Analysis Restricted</p>
                              <p>NutriGuide AI only provides nutritional facts for edible meals, drinks, and ingredients. Nutritional data lookup is disabled for non-food items.</p>
                            </div>
                          </div>

                          <button
                            onClick={resetAll}
                            className="w-full py-2.5 bg-red-600 hover:bg-red-700 text-white text-xs font-bold rounded-lg shadow-sm transition-all flex items-center justify-center gap-1.5"
                          >
                            <Camera className="w-4 h-4" /> Upload a Food Image Instead
                          </button>
                        </div>
                      ) : (
                        <>
                          {!result.classification.is_confident && (
                            <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-3 mb-4 flex items-start gap-2">
                              <AlertTriangle className="w-4 h-4 text-yellow-600 flex-shrink-0 mt-0.5" />
                              <p className="text-sm text-yellow-700">{result.message}</p>
                            </div>
                          )}

                          {/* Multimodal Vision Fallback Card */}
                          {result.gemini_fallback?.available && result.gemini_fallback.suggested_food && (
                            <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4 mb-4">
                              <div className="flex items-center gap-2 mb-1.5">
                                <Sparkles className="w-4 h-4 text-emerald-600" />
                                <span className="text-xs font-bold text-emerald-800 uppercase tracking-wider">
                                  Gemma 3 Multimodal Vision Analysis
                                </span>
                                {result.gemini_fallback.confidence && (
                                  <span className="text-xs bg-emerald-100 text-emerald-800 font-semibold px-2 py-0.5 rounded-full ml-auto">
                                    {result.gemini_fallback.confidence} Confidence
                                  </span>
                                )}
                              </div>
                              <p className="text-sm font-semibold text-emerald-900">
                                Suggested: {result.gemini_fallback.suggested_food}
                              </p>
                              {result.gemini_fallback.explanation && (
                                <p className="text-xs text-emerald-700 mt-1 leading-relaxed">
                                  {result.gemini_fallback.explanation}
                                </p>
                              )}
                              <div className="mt-3 flex items-center gap-2">
                                <button
                                  onClick={() => {
                                    const sugName = result.gemini_fallback!.suggested_food!
                                    const catKey =
                                      result.gemini_fallback?.category_match ||
                                      sugName.toLowerCase().replace(/ /g, '_')
                                    handleSelectAlternative(sugName, catKey)
                                  }}
                                  disabled={loadingNutrition}
                                  className="px-3.5 py-1.5 bg-[#2d6a4f] hover:bg-[#1a3d2b] text-white text-xs font-semibold rounded-lg shadow-sm transition-all flex items-center gap-1.5 disabled:opacity-50"
                                >
                                  <Check className="w-3.5 h-3.5" /> Confirm {result.gemini_fallback.suggested_food} & View Nutrition
                                </button>
                              </div>
                            </div>
                          )}

                          {result.gemini_fallback && !result.gemini_fallback.available && !result.classification.is_confident && (
                            <div className="bg-gray-50 border border-gray-200 rounded-xl p-3 mb-4 text-xs text-gray-600">
                              <p className="font-semibold text-gray-700 mb-0.5">Vision Fallback Unavailable</p>
                              <p>{result.gemini_fallback.error || 'Vision model could not be reached. Please confirm or select your food from the candidates below.'}</p>
                            </div>
                          )}

                          {!result.classification.is_confident && !result.nutrition && (
                            <div className="mt-2 mb-3">
                              <button
                                onClick={() =>
                                  handleSelectAlternative(
                                    result.classification.display_name,
                                    result.classification.predicted_class
                                  )
                                }
                                disabled={loadingNutrition}
                                className="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 text-xs font-medium rounded-lg border border-gray-300 transition-all flex items-center gap-1.5 disabled:opacity-50"
                              >
                                <Check className="w-3.5 h-3.5" /> Confirm {result.classification.display_name} (Local Guess)
                              </button>
                            </div>
                          )}

                          {result.classification.is_confident && result.message && !result.gemini_fallback?.available && (
                            <div className="bg-green-50 border border-green-200 rounded-xl p-3 mb-4 flex items-start gap-2">
                              <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0 mt-0.5" />
                              <p className="text-sm text-green-700">{result.message || 'Food identified successfully.'}</p>
                            </div>
                          )}

                          {/* Top predictions toggle */}
                          {result.classification.top_predictions.length > 1 && (
                            <div className="mt-2">
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
                                    <div key={pred.class} className="flex items-center gap-3 bg-gray-50/70 p-2 rounded-xl">
                                      <span className="text-sm text-gray-700 flex-1 font-medium">{pred.display_name}</span>
                                      <div className="w-24 bg-gray-200 rounded-full h-2">
                                        <div
                                          className="bg-[#52b788] h-2 rounded-full transition-all"
                                          style={{ width: `${pred.confidence * 100}%` }}
                                        />
                                      </div>
                                      <span className="text-xs text-gray-500 w-12 text-right">{pred.confidence_pct}</span>
                                      <button
                                        onClick={() => handleSelectAlternative(pred.display_name, pred.class)}
                                        disabled={loadingNutrition}
                                        className="text-xs font-semibold text-[#2d6a4f] hover:text-white hover:bg-[#2d6a4f] px-2.5 py-1 rounded-lg border border-[#2d6a4f]/30 transition-all flex items-center gap-1 disabled:opacity-50"
                                      >
                                        <Check className="w-3 h-3" /> Select
                                      </button>
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          )}

                          {/* Manual category correction hook */}
                          <div className="mt-4 pt-3 border-t border-gray-100 flex flex-wrap items-center gap-2">
                            <span className="text-xs text-gray-500">Wrong identification?</span>
                            <select
                              disabled={loadingNutrition}
                              onChange={(e) => {
                                const val = e.target.value
                                if (val) {
                                  const key = val.toLowerCase().replace(/ /g, '_')
                                  handleSelectAlternative(val, key)
                                }
                              }}
                              defaultValue=""
                              className="text-xs py-1.5 px-3 rounded-lg border border-gray-200 bg-white text-gray-700 focus:outline-none focus:ring-2 focus:ring-[#52b788] transition-all max-w-[200px]"
                            >
                              <option value="" disabled>Select correct food manually...</option>
                              {allCategories.map((c) => (
                                <option key={c} value={c}>{c}</option>
                              ))}
                            </select>
                            {loadingNutrition && (
                              <span className="text-xs text-[#2d6a4f] animate-pulse">Updating nutrition...</span>
                            )}
                          </div>
                        </>
                      )}
                    </div>
                  </div>
                )
              })()}
            </div>
          </div>

          {/* Feature 2: Clinical Health Safety Advisor Card for Single Dish */}
          {result.health_safety && (
            <HealthSafetyCard
              report={result.health_safety}
              foodName={result.classification.display_name}
            />
          )}

          {/* Nutrition Card */}
          {(result.is_food === false || result.gemini_fallback?.is_food === false) ? (
            <div className="bg-gray-50 border border-gray-200 rounded-2xl p-6 text-center">
              <Ban className="w-8 h-8 text-gray-400 mx-auto mb-2" />
              <p className="text-gray-800 font-semibold text-sm">Nutritional Data Withheld</p>
              <p className="text-xs text-gray-500 mt-1 max-w-md mx-auto">
                Nutritional facts and macros are only calculated for edible meals, drinks, and culinary ingredients.
              </p>
            </div>
          ) : result.nutrition ? (
            <NutritionCard data={result.nutrition} />
          ) : (
            <div className="bg-amber-50/70 border border-amber-200 rounded-2xl p-6 text-center">
              <AlertTriangle className="w-8 h-8 text-amber-500 mx-auto mb-2" />
              <p className="text-amber-900 font-semibold text-sm">Nutritional Data Pending Confirmation</p>
              <p className="text-xs text-amber-700 mt-1 max-w-md mx-auto">
                To ensure accuracy and prevent false dietary claims, definitive nutritional facts are only retrieved after you confirm the food item above.
              </p>
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

      {/* Supported categories footer */}
      <div className="mt-8 bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
        <h4 className="font-semibold text-gray-700 mb-3">Supported Food Categories ({categoryCount})</h4>
        <div className="flex flex-wrap gap-2">
          {allCategories.map((cat) => (
            <span key={cat} className="px-3 py-1 bg-[#e8f4ed] text-[#2d6a4f] text-xs font-medium rounded-full">
              {cat}
            </span>
          ))}
        </div>
        <p className="text-xs text-gray-400 mt-3">
          ✦ MobileNetV3 101 classifier &bull; Multi-item Indian Thali decomposition via Gemma 3 Vision
        </p>
      </div>
    </div>
  )
}
