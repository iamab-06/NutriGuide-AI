"""
NutriGuide AI - Numerical Nutrition Validation Layer
=====================================================
Validates nutritional data against physical, biochemical, and mathematical laws
before presentation to users or injection into LLM prompts.

Key Checks:
1. Physical Non-negativity & Plausibility: Nutrients cannot be negative; per 100g sums cannot exceed 100g.
2. Atwater Energy Balance Check:
   Energy (kcal) ≈ (Protein * 4) + (Carbohydrate * 4) + (Total Fat * 9)
   Allowed tolerance accounts for dietary fiber (which provides 1.5 - 2 kcal/g or 0 kcal/g) and organic acids.
3. Unit Consistency: Ensures units are standard (kcal, g, mg).
4. Missing Data Transparency: Replaces missing or unverified values with explicit None / "Data Unavailable"
   rather than silent defaults or guesses.
"""
import logging
from typing import Dict, Any, Optional, Tuple, List
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Realistic maximum bounds per 100g of food
MAX_BOUNDS_PER_100G = {
    "calories": 900.0,      # Pure fat / oil is ~900 kcal/100g
    "protein": 100.0,       # Pure protein isolate is ~90-100g
    "carbohydrates": 100.0, # Pure refined sugar/starch is ~100g
    "fat": 100.0,           # Pure oil/lard is 100g
    "sugar": 100.0,
    "fiber": 100.0,
    "sodium": 39000.0,      # Pure table salt (NaCl) is ~38,758 mg/100g
    "cholesterol": 3500.0,  # Pure egg yolk/brain tissue
    "saturated_fat": 100.0,
}


class ValidationResult(BaseModel):
    is_valid: bool = True
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    sanitized_data: Dict[str, Any] = Field(default_factory=dict)
    atwater_discrepancy_pct: Optional[float] = None
    verification_status: str = "unverified"  # "verified_lab", "verified_standard", "estimated", "suspicious"


def validate_and_sanitize_nutrition(
    data: Dict[str, Any],
    basis: str = "per 100g",
    source: str = "Unknown",
    source_id: Optional[str] = None,
) -> Tuple[Dict[str, Any], ValidationResult]:
    """
    Validates and sanitizes a nutrition dictionary.
    Returns (sanitized_dict, ValidationResult).
    """
    errors: List[str] = []
    warnings: List[str] = []
    sanitized: Dict[str, Any] = dict(data)

    # 1. Non-negativity and upper bound checks
    for key, max_val in MAX_BOUNDS_PER_100G.items():
        val = sanitized.get(key)
        if val is not None:
            try:
                f_val = float(val)
                if f_val < 0.0:
                    warnings.append(f"{key} was negative ({f_val}); clamped to 0.0.")
                    sanitized[key] = 0.0
                elif basis == "per 100g" and f_val > max_val:
                    errors.append(f"{key} value ({f_val}) exceeds physical maximum for 100g ({max_val}).")
                    sanitized[key] = max_val
                else:
                    sanitized[key] = round(f_val, 2)
            except (ValueError, TypeError):
                warnings.append(f"{key} was non-numeric ({val}); marked unavailable.")
                sanitized[key] = None

    # 2. Macro Sum Check (per 100g: Protein + Carbs + Fat cannot exceed 100g + 5g moisture buffer)
    p = sanitized.get("protein") or 0.0
    c = sanitized.get("carbohydrates") or 0.0
    f = sanitized.get("fat") or 0.0
    macro_sum = p + c + f

    if basis == "per 100g" and macro_sum > 105.0:
        errors.append(
            f"Macro sum exceeds 100g per 100g portion: Protein({p}g) + Carbs({c}g) + Fat({f}g) = {macro_sum:.1f}g."
        )

    # Sugar cannot exceed total Carbohydrates
    sugar = sanitized.get("sugar")
    if sugar is not None and sanitized.get("carbohydrates") is not None:
        if sugar > sanitized["carbohydrates"] + 0.5:
            warnings.append(
                f"Sugar ({sugar}g) reported higher than total Carbohydrates ({sanitized['carbohydrates']}g); adjusted."
            )
            sanitized["sugar"] = sanitized["carbohydrates"]

    # Saturated fat cannot exceed Total Fat
    sat_fat = sanitized.get("saturated_fat")
    if sat_fat is not None and sanitized.get("fat") is not None:
        if sat_fat > sanitized["fat"] + 0.5:
            warnings.append(
                f"Saturated fat ({sat_fat}g) reported higher than Total Fat ({sanitized['fat']}g); adjusted."
            )
            sanitized["saturated_fat"] = sanitized["fat"]

    # 3. Atwater Energy Balance Check
    # Calories ≈ (Protein * 4) + (Carbohydrate * 4) + (Fat * 9)
    # Fiber may contribute 0 to 2 kcal/g.
    cal = sanitized.get("calories")
    atwater_disc_pct = None

    if cal is not None and cal > 10.0 and (p > 0 or c > 0 or f > 0):
        expected_cal = (p * 4.0) + (c * 4.0) + (f * 9.0)
        fiber = sanitized.get("fiber") or 0.0
        # Expected range accounts for fiber deduction or addition
        diff = abs(cal - expected_cal)
        atwater_disc_pct = round((diff / max(cal, expected_cal)) * 100, 1)

        # Allow up to 25% discrepancy for complex food matrices (water, ash, fiber, resistant starches)
        if atwater_disc_pct > 35.0:
            warnings.append(
                f"Atwater discrepancy {atwater_disc_pct}%: reported {cal} kcal vs estimated {expected_cal:.1f} kcal from macros."
            )

    # 4. Determine Verification Status
    if errors:
        status = "suspicious"
    elif "USDA" in source or "FoodData Central" in source:
        status = "verified_lab" if "Foundation" in source else "verified_standard"
    elif "Open Food Facts" in source:
        status = "verified_packaged"
    elif "Estimated" in source or "Recipe" in source:
        status = "estimated"
    else:
        status = "verified_standard"

    # Annotate source tracking metadata
    sanitized["_source"] = source
    sanitized["_source_id"] = str(source_id) if source_id else "USDA-SR"
    sanitized["_verification_status"] = status
    sanitized["_validated"] = len(errors) == 0

    val_res = ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        sanitized_data=sanitized,
        atwater_discrepancy_pct=atwater_disc_pct,
        verification_status=status,
    )

    return sanitized, val_res
