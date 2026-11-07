"""NutriGuide AI - Food Image Analysis Router"""
import logging
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.services.classifier import get_classifier
from app.services.nutrition import get_nutrition_for_food
from app.services.ollama_service import classify_food_with_vision
from app.services.plate_service import decompose_meal_plate_with_vision
from app.services.clinical_advisor import evaluate_food_health_safety
from app.schemas.food import (
    AnalyzeImageResponse,
    ClassificationResult,
    GeminiVisionFallback,
    MealPlateAnalysis,
)
from app.core.categories import CATEGORY_DISPLAY_NAMES, FOOD101_DISPLAY_NAMES

logger = logging.getLogger(__name__)
router = APIRouter()

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_SIZE_MB = 10


def _validate_image_file(file: UploadFile, image_bytes: bytes):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. Allowed: JPEG, PNG, WebP, GIF."
        )

    if file.filename and "." in file.filename:
        ext = file.filename.rsplit(".", 1)[-1].lower()
        if ext not in {"jpg", "jpeg", "png", "webp", "gif"}:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file extension: .{ext}. Allowed: .jpg, .jpeg, .png, .webp, .gif."
            )

    if len(image_bytes) > MAX_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {MAX_SIZE_MB}MB."
        )
    if len(image_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty file uploaded.")


@router.post("/analyze", response_model=AnalyzeImageResponse)
async def analyze_food_image(
    file: UploadFile = File(...),
    conditions: Optional[str] = Form(None),
):
    """
    Analyze a food image: classify it and retrieve nutrition data.
    If local classification confidence is low (< 70%), calls Gemma 3 Vision
    as an intelligent multimodal fallback.
    If conditions are supplied (comma-separated), runs clinical health safety evaluation.
    """
    image_bytes = await file.read()
    _validate_image_file(file, image_bytes)

    # Classify locally
    try:
        classifier = get_classifier()
        prediction = classifier.predict(image_bytes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Classification error: {e}")
        raise HTTPException(status_code=500, detail="Image classification failed. Please try again.")

    classification = ClassificationResult(**prediction)

    cond_list = [c.strip() for c in conditions.split(",") if c.strip()] if conditions else []

    # Nutrition & uncertainty handling
    nutrition = None
    message = ""
    gemini_fb_obj = None
    requires_confirmation = False
    health_safety = None

    if classification.is_confident:
        try:
            nutrition = await get_nutrition_for_food(
                food_name=classification.display_name,
                category_key=classification.predicted_class,
            )
            message = f"Identified as {classification.display_name} with {classification.confidence*100:.1f}% confidence."
            if cond_list and nutrition:
                health_safety = evaluate_food_health_safety(
                    food_name=classification.display_name,
                    nutrition=nutrition,
                    conditions=cond_list,
                    portion_g=100.0,
                )
        except Exception as e:
            logger.error(f"Nutrition retrieval error: {e}")
            message = "Nutrition data temporarily unavailable."
    else:
        # Low confidence / uncertain: trigger Ollama Vision fallback and require confirmation
        requires_confirmation = True
        logger.info(f"Local confidence is below threshold ({classification.confidence*100:.1f}% < {classification.confidence_threshold*100:.0f}%). Triggering Ollama Vision fallback...")
        try:
            fb_res = await classify_food_with_vision(image_bytes)
            gemini_fb_obj = GeminiVisionFallback(**fb_res)
        except Exception as e:
            logger.warning(f"Vision fallback failed: {e}")
            gemini_fb_obj = GeminiVisionFallback(available=False, error=str(e))

        if gemini_fb_obj and gemini_fb_obj.available:
            if not gemini_fb_obj.is_food:
                non_food_label = gemini_fb_obj.suggested_food or "Non-food item"
                message = (
                    f"Non-food item detected: '{non_food_label}'. "
                    "The uploaded image does not appear to contain edible food, beverages, or ingredients. "
                    "Nutritional analysis is not applicable."
                )
                return AnalyzeImageResponse(
                    classification=classification,
                    nutrition=None,
                    message=message,
                    gemini_fallback=gemini_fb_obj,
                    requires_confirmation=False,
                    is_food=False,
                )
            elif gemini_fb_obj.suggested_food:
                sug_name = gemini_fb_obj.suggested_food
                cat_match = gemini_fb_obj.category_match
                disp = CATEGORY_DISPLAY_NAMES.get(cat_match) or FOOD101_DISPLAY_NAMES.get(cat_match) or sug_name

                message = (
                    f"Local model confidence is low ({classification.confidence*100:.1f}% for {classification.display_name}). "
                    f"Ollama Vision suggests '{disp}' ({gemini_fb_obj.confidence} confidence). "
                    "Please confirm your food below to view verified nutrition."
                )
        else:
            message = (
                f"The model's best guess is '{classification.display_name}' "
                f"({classification.confidence*100:.1f}% confidence), but this is below the "
                f"confidence threshold ({classification.confidence_threshold*100:.0f}%). "
                "Please confirm your food or select from alternatives below."
            )

    return AnalyzeImageResponse(
        classification=classification,
        nutrition=nutrition,
        message=message,
        gemini_fallback=gemini_fb_obj,
        requires_confirmation=requires_confirmation,
        is_food=True if not gemini_fb_obj or gemini_fb_obj.is_food else False,
        health_safety=health_safety,
    )


@router.post("/analyze-plate", response_model=MealPlateAnalysis)
async def analyze_meal_plate_image(
    file: UploadFile = File(...),
    conditions: Optional[str] = Form(None),
):
    """
    Decomposes a multi-item meal plate or Indian thali into its individual component dishes,
    estimates portion sizes, retrieves verified ICMR-NIN & USDA nutritional values per component,
    aggregates total meal macronutrients, and screens against active health conditions.
    """
    image_bytes = await file.read()
    _validate_image_file(file, image_bytes)

    cond_list = [c.strip() for c in conditions.split(",") if c.strip()] if conditions else []

    try:
        plate_analysis = await decompose_meal_plate_with_vision(
            image_bytes=image_bytes,
            active_conditions=cond_list,
        )
        return plate_analysis
    except Exception as exc:
        logger.error(f"Plate analysis failed: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Meal plate decomposition failed: {exc}",
        )


