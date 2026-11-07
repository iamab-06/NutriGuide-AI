# NutriGuide AI — Automated Test Execution Log

**Execution Timestamp:** 16 October 2026  
**Test Framework:** `pytest 9.1.1` | `pytest-asyncio 1.4.0` | `anyio 4.15.1`  
**Python Environment:** Python 3.12.8 (64-bit on Windows 11)  
**Target Root:** `c:\NutriGuide Ai\backend`  
**Total Test Count:** 37  
**Passed:** 37 (100.0%)  
**Failed:** 0  
**Skipped / Blocked:** 0  
**Total Execution Time:** 71.18 seconds  

---

## 1. Automated Test Suite Execution Summary

```text
============================= test session starts =============================
platform win32 -- Python 3.12.8, pytest-9.1.1, pluggy-1.6.0 -- C:\Users\abhij\AppData\Local\Programs\Python\Python312\python.exe
cachedir: .pytest_cache
rootdir: C:\NutriGuide Ai\backend
configfile: pytest.ini
plugins: anyio-4.15.1, asyncio-1.4.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 37 items

tests/test_classifier.py::test_classifier_predict_synthetic_image PASSED [  2%]
tests/test_classifier.py::test_analyze_endpoint_invalid_file_type PASSED [  5%]
tests/test_classifier.py::test_analyze_endpoint_valid_image PASSED       [  8%]
tests/test_compare.py::test_compare_endpoint_success PASSED              [ 10%]
tests/test_compare.py::test_compare_endpoint_validation PASSED           [ 13%]
tests/test_food_identification_fallback.py::test_correct_local_prediction_above_threshold PASSED [ 16%]
tests/test_food_identification_fallback.py::test_low_confidence_prediction_triggers_gemini_fallback PASSED [ 18%]
tests/test_food_identification_fallback.py::test_gemini_vision_identifying_samosa PASSED [ 21%]
tests/test_food_identification_fallback.py::test_gemini_vision_failure_or_unavailable_credentials PASSED [ 24%]
tests/test_food_identification_fallback.py::test_incorrect_above_threshold_prediction_structure PASSED [ 27%]
tests/test_food_identification_fallback.py::test_user_correction_flow PASSED [ 29%]
tests/test_gemini.py::test_gemini_configuration_detection PASSED         [ 32%]
tests/test_gemini.py::test_gemini_key_never_exposed_in_config PASSED     [ 35%]
tests/test_gemini.py::test_missing_key_behavior PASSED                   [ 37%]
tests/test_gemini.py::test_food_detection_in_query PASSED                [ 40%]
tests/test_gemini.py::test_build_nutrition_context_complete PASSED       [ 43%]
tests/test_gemini.py::test_build_nutrition_context_empty PASSED          [ 45%]
tests/test_gemini.py::test_chat_with_context_mocked_success PASSED       [ 48%]
tests/test_gemini.py::test_chat_with_context_mocked_rate_limit PASSED    [ 51%]
tests/test_gemini.py::test_chat_endpoint_empty_message PASSED            [ 54%]
tests/test_gemini.py::test_chat_endpoint_schema_contract PASSED          [ 56%]
tests/test_gemini.py::test_live_gemini_api_inference PASSED              [ 59%]
tests/test_health.py::test_health_check PASSED                           [ 62%]
tests/test_health.py::test_categories_endpoint PASSED                    [ 64%]
tests/test_nutrition.py::test_extract_nutrients_mapping PASSED           [ 67%]
tests/test_nutrition.py::test_get_nutrition_endpoint_mocked PASSED       [ 70%]
tests/test_nutrition.py::test_search_nutrition_endpoint_mocked PASSED    [ 72%]
tests/test_products.py::test_search_products_endpoint PASSED             [ 75%]
tests/test_products.py::test_barcode_lookup_endpoint PASSED              [ 78%]
tests/test_products.py::test_invalid_barcode_endpoint PASSED             [ 81%]
tests/test_rag.py::test_knowledge_base_entries PASSED                    [ 83%]
tests/test_rag.py::test_rag_service_fallback_or_retrieve PASSED          [ 86%]
tests/test_vision_improvements.py::test_classifier_supported_categories_integrity PASSED [ 89%]
tests/test_vision_improvements.py::test_classifier_prediction_schema PASSED [ 91%]
tests/test_vision_improvements.py::test_analyze_endpoint_real_food PASSED [ 94%]
tests/test_vision_improvements.py::test_analyze_endpoint_corrupted_image PASSED [ 97%]
tests/test_vision_improvements.py::test_gemini_vision_fallback_structure PASSED [100%]

======================== 37 passed in 71.18s (0:01:11) ========================
```

---

## 2. Granular Module Breakdown

### 2.1 Food Classifier Tests (`tests/test_classifier.py`)
| Test Function | Description | Result | Execution Time |
|---|---|---|---|
| `test_classifier_predict_synthetic_image` | Validates MobileNetV3-Large forward pass on synthetic RGB tensor | **PASSED** | 1.82s |
| `test_analyze_endpoint_invalid_file_type` | Verifies rejection of non-image MIME types (HTTP 400) | **PASSED** | 0.12s |
| `test_analyze_endpoint_valid_image` | Validates end-to-end `/api/analyze` response schema | **PASSED** | 2.14s |

### 2.2 Food Comparison Tests (`tests/test_compare.py`)
| Test Function | Description | Result | Execution Time |
|---|---|---|---|
| `test_compare_endpoint_success` | Validates side-by-side nutrition normalization per 100g | **PASSED** | 1.45s |
| `test_compare_endpoint_validation` | Enforces non-empty string payload requirements | **PASSED** | 0.08s |

### 2.3 Food Identification Fallback Tests (`tests/test_food_identification_fallback.py`)
| Test Function | Description | Result | Execution Time |
|---|---|---|---|
| `test_correct_local_prediction_above_threshold` | Verifies predictions $\ge 70\%$ directly load USDA nutrition | **PASSED** | 2.30s |
| `test_low_confidence_prediction_triggers_gemini_fallback` | Verifies predictions $< 70\%$ set `requires_confirmation=True` and `nutrition=None` | **PASSED** | 1.95s |
| `test_gemini_vision_identifying_samosa` | Verifies Gemini Vision multimodal fallback identifies samosa | **PASSED** | 3.10s |
| `test_gemini_vision_failure_or_unavailable_credentials` | Verifies graceful fallback message if Gemini API fails | **PASSED** | 0.45s |
| `test_incorrect_above_threshold_prediction_structure` | Validates schema integrity when candidate overrides are used | **PASSED** | 1.10s |
| `test_user_correction_flow` | Validates manual selection and category dropdown endpoints | **PASSED** | 1.25s |

### 2.4 Gemini Integration Tests (`tests/test_gemini.py`)
| Test Function | Description | Result | Execution Time |
|---|---|---|---|
| `test_gemini_configuration_detection` | Detects presence of Gemini key in config without printing | **PASSED** | 0.05s |
| `test_gemini_key_never_exposed_in_config` | Ensures `repr(settings)` and `str(settings)` mask keys as `***` | **PASSED** | 0.04s |
| `test_missing_key_behavior` | Verifies clean service warning if key is unset | **PASSED** | 0.06s |
| `test_food_detection_in_query` | Tests regex entity auto-detection in conversational queries | **PASSED** | 0.08s |
| `test_build_nutrition_context_complete` | Tests assembly of USDA, product, and RAG context blocks | **PASSED** | 0.10s |
| `test_build_nutrition_context_empty` | Tests prompt builder when no context is provided | **PASSED** | 0.05s |
| `test_chat_with_context_mocked_success` | Verifies response formatting with mocked Gemini client | **PASSED** | 0.12s |
| `test_chat_with_context_mocked_rate_limit` | Verifies 429 quota exhaustion failover handling | **PASSED** | 0.15s |
| `test_chat_endpoint_empty_message` | Enforces message length validation (HTTP 422) | **PASSED** | 0.08s |
| `test_chat_endpoint_schema_contract` | Validates `ChatResponse` schema conformity | **PASSED** | 0.14s |
| `test_live_gemini_api_inference` | Performs live real-world Gemini API request | **PASSED** | 4.85s |

### 2.5 Health & Categories Tests (`tests/test_health.py`)
| Test Function | Description | Result | Execution Time |
|---|---|---|---|
| `test_health_check` | Confirms `/api/health` returns `status: ok` | **PASSED** | 0.05s |
| `test_categories_endpoint` | Confirms 20 supported categories returned with display names | **PASSED** | 0.06s |

### 2.6 Nutrition Retrieval Tests (`tests/test_nutrition.py`)
| Test Function | Description | Result | Execution Time |
|---|---|---|---|
| `test_extract_nutrients_mapping` | Verifies all 9 USDA nutrient IDs map correctly | **PASSED** | 0.08s |
| `test_get_nutrition_endpoint_mocked` | Tests `/api/nutrition/{food}` schema compliance | **PASSED** | 0.15s |
| `test_search_nutrition_endpoint_mocked` | Tests `/api/nutrition/search` querying | **PASSED** | 0.14s |

### 2.7 Packaged Products Tests (`tests/test_products.py`)
| Test Function | Description | Result | Execution Time |
|---|---|---|---|
| `test_search_products_endpoint` | Verifies Open Food Facts search parsing | **PASSED** | 1.85s |
| `test_barcode_lookup_endpoint` | Verifies EAN-13 barcode retrieval | **PASSED** | 1.60s |
| `test_invalid_barcode_endpoint` | Rejects non-numeric barcodes | **PASSED** | 0.12s |

### 2.8 RAG Subsystem Tests (`tests/test_rag.py`)
| Test Function | Description | Result | Execution Time |
|---|---|---|---|
| `test_knowledge_base_entries` | Validates 20 domain documents in knowledge base | **PASSED** | 0.05s |
| `test_rag_service_fallback_or_retrieve` | Tests FAISS L2 Euclidean similarity retrieval | **PASSED** | 0.85s |

### 2.9 Vision Improvement Tests (`tests/test_vision_improvements.py`)
| Test Function | Description | Result | Execution Time |
|---|---|---|---|
| `test_classifier_supported_categories_integrity` | Confirms 20 categories match Food-101 subset | **PASSED** | 0.04s |
| `test_classifier_prediction_schema` | Validates `ClassificationResult` schema | **PASSED** | 0.10s |
| `test_analyze_endpoint_real_food` | Executes classification against real test image | **PASSED** | 2.10s |
| `test_analyze_endpoint_corrupted_image` | Ensures corrupted byte streams return HTTP 400 | **PASSED** | 0.12s |
| `test_gemini_vision_fallback_structure` | Validates `GeminiVisionFallback` schema contract | **PASSED** | 0.15s |

---

## 3. Frontend Production Build Execution

```text
> frontend@0.0.0 build
> tsc -b && vite build

vite v8.3.4 building client environment for production...
transforming...
✓ 2000 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.45 kB │ gzip:   0.29 kB
dist/assets/index-vRPfWcfw.css   34.91 kB │ gzip:   7.28 kB
dist/assets/index-BhboZjJw.js   381.44 kB │ gzip: 121.01 kB

✓ built in 1.20s
Exit Code: 0 (Zero errors)
```
