"""NutriGuide AI - Food Image Analysis Router"""
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.classifier import get_classifier
from app.services.nutrition import get_nutrition_for_food
from app.schemas.food import AnalyzeImageResponse, ClassificationResult

logger = logging.getLogger(__name__)
router = APIRouter()

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_SIZE_MB = 10


@router.post("/analyze", response_model=AnalyzeImageResponse)
async def analyze_food_image(file: UploadFile = File(...)):
    """
    Analyze a food image: classify it and retrieve nutrition data.
    """
    # Validate file type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. Allowed: JPEG, PNG, WebP, GIF."
        )

    # Read and size-check
    image_bytes = await file.read()
    if len(image_bytes) > MAX_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {MAX_SIZE_MB}MB."
        )
    if len(image_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty file uploaded.")

    # Classify
    try:
        classifier = get_classifier()
        prediction = classifier.predict(image_bytes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Classification error: {e}")
        raise HTTPException(status_code=500, detail="Image classification failed. Please try again.")

    classification = ClassificationResult(**prediction)

    # Retrieve nutrition if confident
    nutrition = None
    message = ""
    if classification.is_confident:
        try:
            nutrition = await get_nutrition_for_food(
                food_name=classification.display_name,
                category_key=classification.predicted_class,
            )
        except Exception as e:
            logger.error(f"Nutrition retrieval error: {e}")
            message = "Nutrition data temporarily unavailable."
    else:
        message = (
            f"The model's best guess is '{classification.display_name}' "
            f"({classification.confidence*100:.1f}% confidence), but this is below the "
            f"confidence threshold ({classification.confidence_threshold*100:.0f}%). "
            "Please confirm the food or search manually."
        )

    return AnalyzeImageResponse(
        classification=classification,
        nutrition=nutrition,
        message=message,
    )
