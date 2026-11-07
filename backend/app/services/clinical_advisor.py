"""
NutriGuide AI - Clinical Condition & Dietary Safety Advisor
Provides evidence-based clinical screening of foods and meal plates against
common chronic health conditions and dietary intolerances.

Based on clinical guidelines from:
- ICMR-NIN (National Institute of Nutrition, India) Dietary Guidelines
- American Diabetes Association (ADA) Standards of Medical Care in Diabetes
- World Health Organization (WHO) Sodium & Saturated Fat Limits
- DASH (Dietary Approaches to Stop Hypertension) Eating Plan
"""

import logging
from typing import List, Dict, Any, Optional
from app.schemas.food import HealthSafetyReport, ConditionEvaluation, NutritionData

logger = logging.getLogger(__name__)

AVAILABLE_CONDITIONS = [
    {
        "id": "diabetes",
        "name": "Type 2 Diabetes / Pre-diabetes",
        "category": "Metabolic",
        "icon": "Activity",
        "description": "Monitors sugar, net carbohydrates, dietary fiber, and estimated glycemic load.",
    },
    {
        "id": "hypertension",
        "name": "Hypertension (High Blood Pressure)",
        "category": "Cardiovascular",
        "icon": "Heart",
        "description": "Screens sodium content against ICMR & WHO single-meal and daily thresholds.",
    },
    {
        "id": "hyperlipidemia",
        "name": "High Cholesterol / Heart Health",
        "category": "Cardiovascular",
        "icon": "ShieldCheck",
        "description": "Evaluates atherogenic saturated fat and dietary cholesterol levels.",
    },
    {
        "id": "gout_uric_acid",
        "name": "High Uric Acid / Gout",
        "category": "Metabolic",
        "icon": "AlertCircle",
        "description": "Screens for high-purine foods (red meats, shellfish, concentrated yeast).",
    },
    {
        "id": "celiac_gluten",
        "name": "Celiac Disease / Gluten Intolerance",
        "category": "Gastrointestinal",
        "icon": "Wheat",
        "description": "Identifies wheat, maida, semolina, barley, rye, and gluten sources.",
    },
    {
        "id": "lactose_intolerance",
        "name": "Lactose Intolerance",
        "category": "Gastrointestinal",
        "icon": "Milk",
        "description": "Screens for milk, cream, cheese, paneer, and unfermented dairy.",
    },
    {
        "id": "weight_management",
        "name": "Weight Loss / Calorie Deficit",
        "category": "Lifestyle",
        "icon": "Flame",
        "description": "Screens caloric density and satiety index (protein + fiber).",
    },
]

# Keywords for ingredient / item classification
GLUTEN_KEYWORDS = [
    "wheat", "maida", "bread", "roti", "chapati", "naan", "paratha", "puri", "bhatura",
    "pasta", "spaghetti", "pizza", "noodle", "ramen", "semolina", "rava", "sooji",
    "barley", "rye", "seitan", "malt", "cookie", "cake", "donut", "pastry", "croissant",
    "samosa", "spring roll", "dumpling"
]

DAIRY_KEYWORDS = [
    "milk", "curd", "yogurt", "cheese", "paneer", "butter", "cream", "ghee",
    "ice cream", "kulfi", "lassi", "buttermilk", "whey", "custard", "cheesecake"
]

HIGH_PURINE_KEYWORDS = [
    "beef", "mutton", "lamb", "pork", "organ meat", "liver", "kidney", "brain",
    "anchovy", "sardine", "mackerel", "herring", "scallop", "mussel", "shrimp",
    "crab", "lobster", "bacon", "sausage", "veal", "duck", "yeast"
]


def evaluate_food_health_safety(
    food_name: str,
    nutrition: Optional[Any],
    conditions: List[str],
    portion_g: float = 100.0,
) -> HealthSafetyReport:
    """
    Evaluates a food item or meal against the user's active clinical conditions.
    Works with NutritionData objects or nutrient dicts.
    """
    if not conditions:
        return HealthSafetyReport(
            overall_status="SAFE",
            summary="No medical conditions or dietary restrictions selected.",
            evaluations=[],
        )

    # Normalize nutrition values scaled to portion
    factor = portion_g / 100.0 if portion_g > 0 else 1.0

    calories = 0.0
    protein = 0.0
    carbs = 0.0
    fat = 0.0
    sugar = 0.0
    fiber = 0.0
    sodium = 0.0
    sat_fat = 0.0
    cholesterol = 0.0

    if nutrition:
        if isinstance(nutrition, dict):
            calories = float(nutrition.get("calories") or 0.0) * factor
            protein = float(nutrition.get("protein") or 0.0) * factor
            carbs = float(nutrition.get("carbohydrates") or 0.0) * factor
            fat = float(nutrition.get("fat") or 0.0) * factor
            sugar = float(nutrition.get("sugar") or 0.0) * factor
            fiber = float(nutrition.get("fiber") or 0.0) * factor
            sodium = float(nutrition.get("sodium") or 0.0) * factor
            sat_fat = float(nutrition.get("saturated_fat") or 0.0) * factor
            cholesterol = float(nutrition.get("cholesterol") or 0.0) * factor
        else:
            calories = float(getattr(nutrition, "calories", 0.0) or 0.0) * factor
            protein = float(getattr(nutrition, "protein", 0.0) or 0.0) * factor
            carbs = float(getattr(nutrition, "carbohydrates", 0.0) or 0.0) * factor
            fat = float(getattr(nutrition, "fat", 0.0) or 0.0) * factor
            sugar = float(getattr(nutrition, "sugar", 0.0) or 0.0) * factor
            fiber = float(getattr(nutrition, "fiber", 0.0) or 0.0) * factor
            sodium = float(getattr(nutrition, "sodium", 0.0) or 0.0) * factor
            sat_fat = float(getattr(nutrition, "saturated_fat", 0.0) or 0.0) * factor
            cholesterol = float(getattr(nutrition, "cholesterol", 0.0) or 0.0) * factor

    net_carbs = max(0.0, carbs - fiber)
    name_low = food_name.lower()

    evaluations: List[ConditionEvaluation] = []
    has_restricted = False
    has_moderate = False

    for cond in conditions:
        cond_id = cond.strip().lower()

        # -------------------------------------------------------------
        # 1. Type 2 Diabetes / Pre-diabetes
        # -------------------------------------------------------------
        if cond_id == "diabetes":
            if sugar >= 12.0 or (net_carbs >= 42.0 and fiber < 3.0):
                status = "RESTRICTED"
                has_restricted = True
                headline = "High Glycemic Impact (Spike Risk)"
                explanation = (
                    f"Contains {sugar:.1f}g sugar and {net_carbs:.1f}g net carbohydrates with only {fiber:.1f}g fiber. "
                    "This high glycemic load can cause rapid blood glucose elevation and insulin resistance stress."
                )
                recommendation = "Restrict portion size, substitute with low-glycemic whole grains (millet/quinoa), or pair with protein and green vegetables."
            elif sugar >= 6.0 or net_carbs >= 22.0:
                status = "MODERATE"
                has_moderate = True
                headline = "Moderate Carbohydrate Load"
                explanation = (
                    f"Provides {net_carbs:.1f}g net carbohydrates and {sugar:.1f}g sugar. "
                    "Acceptable for diabetic management if counted within your total meal carbohydrate budget."
                )
                recommendation = "Eat in moderation. Ensure adequate dietary fiber and avoid sugary beverages alongside this meal."
            else:
                status = "SAFE"
                headline = "Glycemic Friendly"
                explanation = (
                    f"Low sugar ({sugar:.1f}g) and low net carbohydrates ({net_carbs:.1f}g) with {fiber:.1f}g fiber. "
                    "Minimal impact on post-meal blood glucose levels."
                )
                recommendation = "Suitable for diabetic meal planning."

            evaluations.append(ConditionEvaluation(
                condition_id="diabetes",
                condition_name="Type 2 Diabetes / Pre-diabetes",
                status=status,
                headline=headline,
                explanation=explanation,
                recommendation=recommendation,
            ))

        # -------------------------------------------------------------
        # 2. Hypertension (High Blood Pressure)
        # -------------------------------------------------------------
        elif cond_id == "hypertension":
            daily_pct = (sodium / 2000.0) * 100.0 if sodium > 0 else 0.0
            if sodium >= 650.0:
                status = "RESTRICTED"
                has_restricted = True
                headline = "High Sodium Warning"
                explanation = (
                    f"Delivers {sodium:.0f}mg sodium ({daily_pct:.0f}% of WHO 2000mg daily ceiling in a single serving). "
                    "High dietary sodium contributes to fluid retention and acute vascular pressure."
                )
                recommendation = "Avoid adding extra table salt. Drink plenty of water and prioritize potassium-rich vegetables."
            elif sodium >= 300.0:
                status = "MODERATE"
                has_moderate = True
                headline = "Moderate Sodium Content"
                explanation = (
                    f"Contains {sodium:.0f}mg sodium ({daily_pct:.0f}% of daily allowance). "
                    "Acceptable if total daily salt intake is monitored carefully."
                )
                recommendation = "Balance with low-sodium foods across the remainder of the day."
            else:
                status = "SAFE"
                headline = "Heart-Healthy Low Sodium"
                explanation = (
                    f"Contains {sodium:.0f}mg sodium ({daily_pct:.0f}% of daily allowance). "
                    "Complies with DASH diet and ICMR cardiovascular recommendations."
                )
                recommendation = "Excellent choice for blood pressure management."

            evaluations.append(ConditionEvaluation(
                condition_id="hypertension",
                condition_name="Hypertension (Blood Pressure)",
                status=status,
                headline=headline,
                explanation=explanation,
                recommendation=recommendation,
            ))

        # -------------------------------------------------------------
        # 3. High Cholesterol / Heart Health
        # -------------------------------------------------------------
        elif cond_id in {"hyperlipidemia", "cholesterol", "heart"}:
            if sat_fat >= 5.0 or cholesterol >= 70.0:
                status = "RESTRICTED"
                has_restricted = True
                headline = "Atherogenic Lipid Warning"
                explanation = (
                    f"Contains {sat_fat:.1f}g saturated fat and {cholesterol:.0f}mg dietary cholesterol. "
                    "Excessive saturated fatty acids can increase circulating LDL cholesterol levels."
                )
                recommendation = "Limit portion, choose plant-based fats or lean preparation methods (steaming/baking instead of frying)."
            elif sat_fat >= 2.0 or cholesterol >= 25.0:
                status = "MODERATE"
                has_moderate = True
                headline = "Moderate Saturated Fat"
                explanation = (
                    f"Provides {sat_fat:.1f}g saturated fat and {cholesterol:.0f}mg cholesterol. "
                    "Consume as an occasional component rather than daily staple."
                )
                recommendation = "Balance with monounsaturated fats (nuts, seeds, olive oil)."
            else:
                status = "SAFE"
                headline = "Cardiovascular Friendly"
                explanation = (
                    f"Low in saturated fat ({sat_fat:.1f}g) and low cholesterol ({cholesterol:.0f}mg). "
                    "Supports healthy blood lipid profiles."
                )
                recommendation = "Heart-conscious selection."

            evaluations.append(ConditionEvaluation(
                condition_id="hyperlipidemia",
                condition_name="High Cholesterol / Heart Health",
                status=status,
                headline=headline,
                explanation=explanation,
                recommendation=recommendation,
            ))

        # -------------------------------------------------------------
        # 4. Gout / High Uric Acid
        # -------------------------------------------------------------
        elif cond_id in {"gout_uric_acid", "gout", "uric_acid"}:
            is_high_purine = any(term in name_low for term in HIGH_PURINE_KEYWORDS)
            if is_high_purine:
                status = "RESTRICTED"
                has_restricted = True
                headline = "High Purine Warning (Gout Flare Risk)"
                explanation = (
                    f"'{food_name}' contains ingredients recognized as high in purine compounds. "
                    "Metabolism of purines yields uric acid, which can precipitate into joint crystals."
                )
                recommendation = "Replace with low-purine proteins like low-fat dairy, eggs, tofu, or moderate lentils with high hydration."
            elif protein >= 25.0:
                status = "MODERATE"
                has_moderate = True
                headline = "Moderate Purine Density"
                explanation = (
                    f"High protein density ({protein:.1f}g). Ensure adequate water intake to facilitate uric acid clearance."
                )
                recommendation = "Drink 2.5-3 liters of water daily to support renal excretion."
            else:
                status = "SAFE"
                headline = "Low Purine Profile"
                explanation = "Free from concentrated purine sources; safe for maintaining stable serum uric acid."
                recommendation = "Safe for gout-conscious diets."

            evaluations.append(ConditionEvaluation(
                condition_id="gout_uric_acid",
                condition_name="High Uric Acid / Gout",
                status=status,
                headline=headline,
                explanation=explanation,
                recommendation=recommendation,
            ))

        # -------------------------------------------------------------
        # 5. Celiac Disease / Gluten Sensitivity
        # -------------------------------------------------------------
        elif cond_id in {"celiac_gluten", "gluten", "celiac"}:
            is_gluten = any(term in name_low for term in GLUTEN_KEYWORDS)
            if is_gluten:
                status = "RESTRICTED"
                has_restricted = True
                headline = "Contains Gluten (Unsafe for Celiac)"
                explanation = (
                    f"'{food_name}' contains wheat, maida, semolina, or gluten-containing grains. "
                    "Can trigger intestinal inflammation and immune responses in celiac patients."
                )
                recommendation = "Opt for certified gluten-free alternatives: rice, millets (ragi, jowar, bajra), or corn-based preparations."
            else:
                status = "SAFE"
                headline = "Naturally Gluten-Free"
                explanation = f"'{food_name}' is typically prepared from naturally gluten-free ingredients (rice, dal, vegetable, or dairy)."
                recommendation = "Verify no cross-contamination occurred during commercial preparation."

            evaluations.append(ConditionEvaluation(
                condition_id="celiac_gluten",
                condition_name="Celiac Disease / Gluten Sensitivity",
                status=status,
                headline=headline,
                explanation=explanation,
                recommendation=recommendation,
            ))

        # -------------------------------------------------------------
        # 6. Lactose Intolerance
        # -------------------------------------------------------------
        elif cond_id in {"lactose_intolerance", "lactose", "dairy"}:
            is_dairy = any(term in name_low for term in DAIRY_KEYWORDS)
            if is_dairy:
                if any(k in name_low for k in ["curd", "yogurt", "ghee", "hard cheese"]):
                    status = "MODERATE"
                    has_moderate = True
                    headline = "Fermented Dairy (Low Lactose)"
                    explanation = (
                        f"'{food_name}' is a fermented or clarified dairy item. Bacterial fermentation reduces lactose content significantly."
                    )
                    recommendation = "Often well tolerated in small servings, but monitor personal sensitivity."
                else:
                    status = "RESTRICTED"
                    has_restricted = True
                    headline = "Contains Lactose"
                    explanation = f"'{food_name}' contains milk, cream, or dairy products with unfermented lactose."
                    recommendation = "Use lactase enzyme drops or choose plant milks (almond, soy, oat milk) or tofu."
            else:
                status = "SAFE"
                headline = "Dairy & Lactose-Free"
                explanation = f"'{food_name}' contains no dairy ingredients. Safe for lactose-intolerant individuals."
                recommendation = "Safe to consume."

            evaluations.append(ConditionEvaluation(
                condition_id="lactose_intolerance",
                condition_name="Lactose Intolerance",
                status=status,
                headline=headline,
                explanation=explanation,
                recommendation=recommendation,
            ))

        # -------------------------------------------------------------
        # 7. Weight Management / Calorie Control
        # -------------------------------------------------------------
        elif cond_id in {"weight_management", "weight_loss", "calories"}:
            cal_per_100g = (calories / factor) if factor > 0 else calories
            if cal_per_100g >= 350.0:
                status = "RESTRICTED"
                has_restricted = True
                headline = "High Calorie Density"
                explanation = (
                    f"Delivers {cal_per_100g:.0f} kcal per 100g with high fat/sugar ratio. "
                    "Consuming high-density foods makes remaining in a calorie deficit challenging."
                )
                recommendation = "Enjoy small mindful portions. Pair with low-calorie volume foods like cucumbers, salad, or clear soup."
            elif cal_per_100g >= 180.0:
                status = "MODERATE"
                has_moderate = True
                headline = "Moderate Energy Density"
                explanation = (
                    f"Delivers {cal_per_100g:.0f} kcal per 100g with {protein:.1f}g protein and {fiber:.1f}g fiber. "
                    "Fits well within daily macronutrient allowances."
                )
                recommendation = "Measure portions accurately using katori or measuring cup."
            else:
                status = "SAFE"
                headline = "High Satiety / Low Energy Density"
                explanation = (
                    f"Calorie-conscious ({cal_per_100g:.0f} kcal per 100g) with favorable volume. "
                    "Supports satiety without excessive calorie intake."
                )
                recommendation = "Ideal choice for fat loss and healthy weight management."

            evaluations.append(ConditionEvaluation(
                condition_id="weight_management",
                condition_name="Weight Management",
                status=status,
                headline=headline,
                explanation=explanation,
                recommendation=recommendation,
            ))

    # Determine overall status
    if has_restricted:
        overall_status = "RESTRICTED"
        summary = (
            f"Caution advised for {food_name}: conflicts with one or more of your active health conditions. "
            "Review specific warnings and suggested alternatives below."
        )
    elif has_moderate:
        overall_status = "MODERATE"
        summary = (
            f"{food_name} is acceptable in moderate portion sizes. "
            "Follow the clinical recommendations below to optimize nutritional balance."
        )
    else:
        overall_status = "SAFE"
        summary = (
            f"{food_name} aligns well with your active health conditions. "
            "Nutritionally favorable with no critical contraindications detected."
        )

    return HealthSafetyReport(
        overall_status=overall_status,
        summary=summary,
        evaluations=evaluations,
    )
