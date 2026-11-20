"""
NutriGuide AI - Karnataka Food Nutrition & Database Unit Tests
==============================================================
Validates:
1. All 15 Karnataka regional dishes exist in the Curated Local Database.
2. Canonical names, aliases, and regional names map correctly.
3. Nutrient composition (calories, protein, carbs, fat, fiber, sodium, sugar)
   per 100g satisfies Atwater caloric balance (<5% discrepancy).
4. Substring and false-positive collision resistance:
   - Mysore Pak does NOT return Chinese Cabbage (pak-choi).
   - Mangalore Buns does NOT return Bao Bun.
   - Neer Dosa does NOT collide with Plain Dosa or Masala Dosa.
   - Punctuation/hyphen variations (e.g. bisi-bele-bath, mysore_pak) match.
5. End-to-end retrieval via get_nutrition_for_food service function.
"""
import pytest
import asyncio
from app.data.food_database import get_local_food_db, CURATED_FOOD_RECORDS
from app.services.nutrition import get_nutrition_for_food, search_food

KARNATAKA_DISH_IDS = [
    "bisi_bele_bath",
    "ragi_mudde",
    "akki_rotti",
    "jolada_rotti",
    "mysore_pak",
    "dharwad_peda",
    "maddur_vada",
    "neer_dosa",
    "donne_biryani",
    "holige_obbattu",
    "rava_idli",
    "kesari_bath",
    "mangalore_buns",
    "chitranna",
    "karnataka_sambar",
]

KARNATAKA_TEST_QUERIES = [
    # (search_term, expected_id, expected_keyword_in_name)
    ("Bisi Bele Bath", "bisi_bele_bath", "Bisi Bele Bath"),
    ("bisi-bele-bath", "bisi_bele_bath", "Bisi Bele Bath"),
    ("bisibelebath", "bisi_bele_bath", "Bisi Bele Bath"),
    ("Ragi Mudde", "ragi_mudde", "Ragi Mudde"),
    ("ragi ball", "ragi_mudde", "Ragi Mudde"),
    ("Akki Rotti", "akki_rotti", "Akki Rotti"),
    ("akki roti", "akki_rotti", "Akki Rotti"),
    ("Jolada Rotti", "jolada_rotti", "Jolada Rotti"),
    ("jowar roti", "jolada_rotti", "Jolada Rotti"),
    ("Mysore Pak", "mysore_pak", "Mysore Pak"),
    ("mysore_pak", "mysore_pak", "Mysore Pak"),
    ("mysore-pak", "mysore_pak", "Mysore Pak"),
    ("Dharwad Peda", "dharwad_peda", "Dharwad Peda"),
    ("dharwad pedha", "dharwad_peda", "Dharwad Peda"),
    ("Maddur Vada", "maddur_vada", "Maddur Vada"),
    ("maddur vade", "maddur_vada", "Maddur Vada"),
    ("Neer Dosa", "neer_dosa", "Neer Dosa"),
    ("neer dose", "neer_dosa", "Neer Dosa"),
    ("mangalore neer dosa", "neer_dosa", "Neer Dosa"),
    ("Donne Biryani", "donne_biryani", "Donne Biryani"),
    ("bangalore donne biryani", "donne_biryani", "Donne Biryani"),
    ("Holige", "holige_obbattu", "Holige"),
    ("Obbattu", "holige_obbattu", "Obbattu"),
    ("Rava Idli", "rava_idli", "Rava Idli"),
    ("mtr rava idli", "rava_idli", "Rava Idli"),
    ("Kesari Bath", "kesari_bath", "Kesari Bath"),
    ("rava kesari", "kesari_bath", "Kesari Bath"),
    ("Mangalore Buns", "mangalore_buns", "Mangalore Buns"),
    ("mangaluru buns", "mangalore_buns", "Mangalore Buns"),
    ("Chitranna", "chitranna", "Chitranna"),
    ("lemon rice", "chitranna", "Chitranna"),
    ("Karnataka Sambar", "karnataka_sambar", "Karnataka Sambar"),
    ("udupi sambar", "karnataka_sambar", "Karnataka Sambar"),
]


def test_all_15_karnataka_foods_present_in_curated_records():
    """Verify that all 15 required Karnataka foods are registered in CURATED_FOOD_RECORDS."""
    record_ids = {r["id"] for r in CURATED_FOOD_RECORDS}
    for dish_id in KARNATAKA_DISH_IDS:
        assert dish_id in record_ids, f"Missing required Karnataka food in CURATED_FOOD_RECORDS: {dish_id}"


def test_sqlite_database_persistence():
    """Verify all 15 foods are stored in SQLite and retrievable by get_by_id."""
    db = get_local_food_db()
    for dish_id in KARNATAKA_DISH_IDS:
        record = db.get_by_id(dish_id)
        assert record is not None, f"Could not find {dish_id} in SQLite database"
        assert record["calories"] > 0
        assert record["protein"] is not None
        assert record["carbohydrates"] is not None
        assert record["fat"] is not None
        assert record["source_id"].startswith("KA-IFCT-")


def test_atwater_caloric_balance_for_karnataka_foods():
    """Verify that each Karnataka food's macros align with Atwater factor (4-4-9) within 5%."""
    db = get_local_food_db()
    for dish_id in KARNATAKA_DISH_IDS:
        record = db.get_by_id(dish_id)
        cal = record["calories"]
        p = record["protein"]
        c = record["carbohydrates"]
        f = record["fat"]
        calc_cal = round((p * 4.0) + (c * 4.0) + (f * 9.0), 2)
        diff_pct = abs(calc_cal - cal) / cal * 100.0
        assert diff_pct <= 5.0, (
            f"{dish_id}: Atwater calculated {calc_cal} kcal vs stated {cal} kcal "
            f"exceeds 5% tolerance (was {diff_pct:.2f}%)"
        )


@pytest.mark.parametrize("query, expected_id, expected_keyword", KARNATAKA_TEST_QUERIES)
def test_search_by_term_karnataka_foods(query, expected_id, expected_keyword):
    """Verify multi-tier matching identifies Karnataka foods by various search terms and aliases."""
    db = get_local_food_db()
    match = db.search_by_term(query)
    assert match is not None, f"Failed to match query '{query}'"
    assert match["id"] == expected_id, f"Query '{query}' matched {match['id']} instead of {expected_id}"
    assert expected_keyword.lower() in match["canonical_name"].lower()


def test_prevention_of_false_substring_collisions():
    """Verify that specific dangerous false substring collisions are avoided."""
    db = get_local_food_db()

    # 1. Neer Dosa vs Plain Dosa vs Masala Dosa
    neer = db.search_by_term("neer dosa")
    assert neer is not None and neer["id"] == "neer_dosa"

    plain = db.search_by_term("plain dosa")
    assert plain is not None and plain["id"] == "dosa_plain"

    # 2. Mysore Pak vs Pak Choi / other pak
    mysore = db.search_by_term("mysore pak")
    assert mysore is not None and mysore["id"] == "mysore_pak"
    assert "cabbage" not in mysore["canonical_name"].lower()

    # 3. Mangalore Buns vs Bao Bun
    buns = db.search_by_term("mangalore buns")
    assert buns is not None and buns["id"] == "mangalore_buns"
    assert "bao" not in buns["canonical_name"].lower()


@pytest.mark.asyncio
async def test_get_nutrition_for_food_karnataka():
    """Verify full end-to-end nutrition service retrieval for Karnataka foods."""
    res_mysore = await get_nutrition_for_food("Mysore Pak")
    assert res_mysore is not None
    assert res_mysore.data_available is True
    assert "Mysore Pak" in res_mysore.food_name
    assert res_mysore.calories == 524.0
    assert "Cabbage" not in res_mysore.food_name

    res_buns = await get_nutrition_for_food("Mangalore Buns")
    assert res_buns is not None
    assert res_buns.data_available is True
    assert "Mangalore Buns" in res_buns.food_name
    assert res_buns.calories == 315.0
    assert "Bao" not in res_buns.food_name

    res_mudde = await get_nutrition_for_food("Ragi Mudde")
    assert res_mudde is not None
    assert res_mudde.data_available is True
    assert "Ragi Mudde" in res_mudde.food_name
    assert res_mudde.fiber >= 4.0
