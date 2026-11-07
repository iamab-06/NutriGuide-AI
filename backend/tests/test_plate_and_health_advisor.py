"""
NutriGuide AI - Tests for:
Feature 1: Multi-Item Meal Plate / Thali Decomposition ("Meal Plate Scanner")
Feature 2: Clinical Condition & Health Safety Advisor ("Can I Eat This?")
Tests multiple diverse samples (Indian Thali, Breakfast combo, Western plate, clinical food evaluations).
"""

import io
import json
import pytest
from unittest.mock import patch, MagicMock
from PIL import Image
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.services.clinical_advisor import (
    evaluate_food_health_safety,
    AVAILABLE_CONDITIONS,
)
from app.services.plate_service import decompose_meal_plate_with_vision
from app.schemas.food import NutritionData


def create_test_image(size=(256, 256), color=(100, 150, 200)) -> bytes:
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


# =========================================================================
# FEATURE 2 TESTS: CLINICAL CONDITION HEALTH SAFETY ADVISOR
# =========================================================================

def test_available_conditions_metadata():
    """Verify all 7 supported chronic conditions are properly cataloged."""
    cond_ids = [c["id"] for c in AVAILABLE_CONDITIONS]
    assert "diabetes" in cond_ids
    assert "hypertension" in cond_ids
    assert "hyperlipidemia" in cond_ids
    assert "gout_uric_acid" in cond_ids
    assert "celiac_gluten" in cond_ids
    assert "lactose_intolerance" in cond_ids
    assert "weight_management" in cond_ids


def test_diabetes_screening_high_sugar():
    """Sample A: High sugar confection (Gulab Jamun / Tiramisu) triggers RESTRICTED for Diabetes."""
    nutr = {
        "calories": 360,
        "protein": 5.0,
        "carbohydrates": 55.0,
        "fat": 15.0,
        "sugar": 32.0,  # High sugar (>12g)
        "fiber": 1.0,
        "sodium": 120,
    }
    report = evaluate_food_health_safety(
        food_name="Gulab Jamun",
        nutrition=nutr,
        conditions=["diabetes"],
        portion_g=100.0,
    )
    assert report.overall_status == "RESTRICTED"
    assert len(report.evaluations) == 1
    ev = report.evaluations[0]
    assert ev.condition_id == "diabetes"
    assert ev.status == "RESTRICTED"
    assert "High Glycemic Impact" in ev.headline


def test_hypertension_screening_high_sodium():
    """Sample B: High sodium food (Salted French Fries / Instant Ramen) triggers RESTRICTED for Hypertension."""
    nutr = {
        "calories": 312,
        "protein": 3.4,
        "carbohydrates": 41.0,
        "fat": 15.0,
        "sodium": 820,  # High sodium (>650mg)
    }
    report = evaluate_food_health_safety(
        food_name="Salted French Fries",
        nutrition=nutr,
        conditions=["hypertension"],
        portion_g=100.0,
    )
    assert report.overall_status == "RESTRICTED"
    ev = report.evaluations[0]
    assert ev.status == "RESTRICTED"
    assert "High Sodium Warning" in ev.headline
    assert "820mg sodium" in ev.explanation


def test_celiac_and_gluten_screening():
    """Sample C: Wheat Roti vs Naturally Gluten-Free Rice/Idli."""
    # Wheat roti contains gluten
    roti_report = evaluate_food_health_safety(
        food_name="Wheat Chapati Roti",
        nutrition={"calories": 120, "protein": 3.5, "carbohydrates": 24, "fat": 1.5},
        conditions=["celiac_gluten"],
    )
    assert roti_report.overall_status == "RESTRICTED"
    assert "Contains Gluten" in roti_report.evaluations[0].headline

    # Steamed rice / idli is naturally gluten-free
    idli_report = evaluate_food_health_safety(
        food_name="Steamed Rice Idli",
        nutrition={"calories": 140, "protein": 4.0, "carbohydrates": 28, "fat": 0.5},
        conditions=["celiac_gluten"],
    )
    assert idli_report.overall_status == "SAFE"
    assert "Naturally Gluten-Free" in idli_report.evaluations[0].headline


def test_gout_purine_screening():
    """Sample D: High purine red meat (Mutton Rogan Josh) triggers Gout warning."""
    report = evaluate_food_health_safety(
        food_name="Mutton Rogan Josh",
        nutrition={"calories": 280, "protein": 22.0, "carbohydrates": 6, "fat": 19},
        conditions=["gout_uric_acid"],
    )
    assert report.overall_status == "RESTRICTED"
    assert "High Purine Warning" in report.evaluations[0].headline


def test_lactose_intolerance_screening():
    """Sample E: Paneer Curry (Dairy) triggers Lactose Intolerance warning."""
    report = evaluate_food_health_safety(
        food_name="Paneer Butter Masala",
        nutrition={"calories": 320, "protein": 11.0, "carbohydrates": 10, "fat": 26},
        conditions=["lactose_intolerance"],
    )
    assert report.overall_status == "RESTRICTED"
    assert "Contains Lactose" in report.evaluations[0].headline


@pytest.mark.asyncio
async def test_health_advisor_api_endpoint():
    """Verify POST /api/health-advisor/evaluate endpoint returns clinical evaluation."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Fetch conditions list
        res_cond = await ac.get("/api/health-advisor/conditions")
        assert res_cond.status_code == 200
        conds = res_cond.json()
        assert len(conds) >= 7

        # 2. Evaluate a food item (Samosa: fried, high sodium, gluten)
        payload = {
            "food_name": "Samosa",
            "category_key": "samosa",
            "conditions": ["diabetes", "hypertension", "celiac_gluten"],
            "portion_g": 100.0,
        }
        res_eval = await ac.post("/api/health-advisor/evaluate", json=payload)
        assert res_eval.status_code == 200
        data = res_eval.json()
        assert data["overall_status"] in ["SAFE", "MODERATE", "RESTRICTED"]
        assert len(data["evaluations"]) == 3


# =========================================================================
# FEATURE 1 TESTS: MULTI-ITEM MEAL PLATE / THALI DECOMPOSITION
# =========================================================================

@pytest.mark.asyncio
async def test_indian_thali_plate_decomposition():
    """
    Sample 1: Decompose a complete South Indian Lunch Thali:
    Steamed Rice (150g) + Sambar (100g) + Beetroot Palya (60g) + Curd (50g) + Chapati (40g).
    Verifies item segmentation, nutrient scaling, and total meal aggregation.
    """
    mock_thali_json = {
        "is_food": True,
        "is_plate": True,
        "meal_title": "South Indian Vegetarian Thali",
        "visual_summary": "Complete thali plate containing steamed white rice, lentil vegetable sambar, beetroot palya, plain curd, and one chapati.",
        "items": [
            {
                "name": "Steamed Rice",
                "category_guess": "rice",
                "estimated_portion_g": 150,
                "serving_description": "1 medium bowl (~150g)",
                "notes": "White basmati rice in center",
            },
            {
                "name": "Sambar",
                "category_guess": "sambar",
                "estimated_portion_g": 100,
                "serving_description": "1 katori bowl (~100g)",
                "notes": "Lentil stew with drumsticks and tomatoes",
            },
            {
                "name": "Beetroot Palya",
                "category_guess": "vegetable_curry",
                "estimated_portion_g": 60,
                "serving_description": "Small side serving (~60g)",
                "notes": "Spiced beetroot stir-fry with grated coconut",
            },
            {
                "name": "Plain Curd",
                "category_guess": "yogurt",
                "estimated_portion_g": 50,
                "serving_description": "Small katori (~50g)",
                "notes": "Unsweetened fresh curd",
            },
            {
                "name": "Chapati Roti",
                "category_guess": "roti",
                "estimated_portion_g": 40,
                "serving_description": "1 piece (~40g)",
                "notes": "Whole wheat flatbread",
            },
        ],
    }

    img_bytes = create_test_image()

    with patch("app.services.plate_service._ollama_chat", return_value=json.dumps(mock_thali_json)):
        result = await decompose_meal_plate_with_vision(
            image_bytes=img_bytes,
            active_conditions=["diabetes", "hypertension"],
        )

    assert result.is_plate is True
    assert result.meal_title == "South Indian Vegetarian Thali"
    assert result.items_detected_count == 5
    assert len(result.components) == 5

    # Check component names
    names = [c.name for c in result.components]
    assert "Steamed Rice" in names
    assert "Sambar" in names
    assert "Chapati Roti" in names

    # Total calories and macros must be aggregated
    assert result.total_calories > 250.0
    assert result.total_protein > 5.0
    assert result.total_carbohydrates > 40.0
    assert result.macro_ratios["carbohydrates_pct"] > 0
    assert result.macro_ratios["protein_pct"] > 0

    # Clinical health safety for the complete meal plate
    assert result.health_safety is not None
    assert len(result.health_safety.evaluations) == 2


@pytest.mark.asyncio
async def test_south_indian_breakfast_combo_plate():
    """
    Sample 2: Decompose a South Indian Breakfast Plate:
    Idli (100g, 2 pieces) + Meduvada (45g, 1 piece) + Coconut Chutney (30g) + Sambar (80g).
    """
    mock_breakfast_json = {
        "is_food": True,
        "is_plate": True,
        "meal_title": "Idli Vada Breakfast Combo Plate",
        "visual_summary": "Two steamed idlis, one golden crispy meduvada, served with fresh coconut chutney and hot sambar.",
        "items": [
            {
                "name": "Steamed Idli",
                "category_guess": "idli",
                "estimated_portion_g": 100,
                "serving_description": "2 medium idlis (~100g)",
                "notes": "Steamed fermented rice and urad dal cakes",
            },
            {
                "name": "Meduvada",
                "category_guess": "vada",
                "estimated_portion_g": 45,
                "serving_description": "1 crispy vada (~45g)",
                "notes": "Deep fried spiced lentil donut",
            },
            {
                "name": "Coconut Chutney",
                "category_guess": "chutney",
                "estimated_portion_g": 30,
                "serving_description": "2 tablespoons (~30g)",
                "notes": "Fresh ground coconut with mustard seed tadka",
            },
        ],
    }

    img_bytes = create_test_image()

    with patch("app.services.plate_service._ollama_chat", return_value=json.dumps(mock_breakfast_json)):
        result = await decompose_meal_plate_with_vision(
            image_bytes=img_bytes,
            active_conditions=["celiac_gluten"],
        )

    assert result.is_plate is True
    assert result.items_detected_count == 3
    # Idli, vada, coconut chutney are typically gluten-free
    assert result.total_calories > 150.0


@pytest.mark.asyncio
async def test_plate_api_endpoint():
    """Verify POST /api/analyze-plate endpoint decomposes plates and returns aggregated macros."""
    mock_plate_json = {
        "is_food": True,
        "is_plate": True,
        "meal_title": "Continental Dinner Plate",
        "visual_summary": "Grilled salmon fillet with steamed broccoli florets and roasted potatoes.",
        "items": [
            {
                "name": "Grilled Salmon",
                "category_guess": "salmon",
                "estimated_portion_g": 150,
                "serving_description": "1 fillet (~150g)",
                "notes": "Grilled with herbs",
            },
            {
                "name": "Steamed Broccoli",
                "category_guess": "broccoli",
                "estimated_portion_g": 80,
                "serving_description": "1 cup florets (~80g)",
                "notes": "Tender steamed greens",
            },
        ],
    }

    img_bytes = create_test_image()

    with patch("app.services.plate_service._ollama_chat", return_value=json.dumps(mock_plate_json)):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post(
                "/api/analyze-plate",
                files={"file": ("dinner.jpg", img_bytes, "image/jpeg")},
                data={"conditions": "diabetes,hypertension"},
            )

    assert response.status_code == 200
    data = response.json()
    assert data["is_plate"] is True
    assert data["meal_title"] == "Continental Dinner Plate"
    assert data["items_detected_count"] == 2
    assert data["total_calories"] > 100.0
    assert data["health_safety"] is not None
