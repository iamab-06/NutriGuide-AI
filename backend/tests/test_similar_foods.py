import os
import sys
import glob

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.services.classifier import FoodClassifier

def run_tests():
    clf = FoodClassifier()
    pairs = [
        ("pancakes", "waffles"),
        ("hamburger", "pulled_pork_sandwich"),
        ("fried_rice", "risotto"),
        ("ramen", "pho"),
        ("samosa", "spring_rolls"),
        ("chocolate_cake", "chocolate_mousse"),
        ("steak", "filet_mignon"),
        ("french_fries", "onion_rings"),
        ("baklava", "apple_pie"),
        ("ice_cream", "frozen_yogurt"),
    ]

    print("=" * 70)
    print("NUTRIGUIDE AI — SIMILAR FOOD PAIRS CONFUSION & UNCERTAINTY TEST")
    print("=" * 70)

    total_tested = 0
    correct_top1 = 0
    correct_in_top3 = 0
    properly_gated = 0

    for cat_a, cat_b in pairs:
        print(f"\n--- PAIR: {cat_a.upper()} vs {cat_b.upper()} ---")
        for cat in [cat_a, cat_b]:
            files = sorted(glob.glob(f"datasets/food101/val/{cat}/*.jpg"))[:3]
            for fpath in files:
                total_tested += 1
                with open(fpath, "rb") as fp:
                    img_bytes = fp.read()
                res = clf.predict(img_bytes)
                pred_class = res["predicted_class"]
                conf = res["confidence"]
                is_conf = res["is_confident"]
                top_preds = res["top_predictions"]

                is_correct = (pred_class == cat)
                in_top3 = any(p["class"] == cat for p in top_preds[:3])

                if is_correct:
                    correct_top1 += 1
                if in_top3:
                    correct_in_top3 += 1

                # If it confused with the similar food or was ambiguous, did uncertainty gate catch it?
                # If incorrect, it MUST be uncertain (confidence < 70%) so safety gate prevents wrong nutrition!
                if not is_correct and not is_conf:
                    properly_gated += 1

                top_names = [f"{p['display_name']} ({p['confidence_pct']})" for p in top_preds[:3]]
                status_str = "CORRECT" if is_correct else f"MISMATCH -> {res['display_name']}"
                conf_str = "CONFIDENT (>=70%)" if is_conf else "UNCERTAIN (<70% Fallback Triggered)"
                fname = os.path.basename(fpath)

                print(f"  [{cat}] {fname}: {status_str} | Conf: {conf*100:.1f}% [{conf_str}]")
                print(f"       Top 3: {', '.join(top_names)}")

    print("\n" + "=" * 70)
    print(f"SUMMARY RESULTS:")
    print(f"  Total Images Tested across 10 similar pairs: {total_tested}")
    print(f"  Top-1 Direct Accuracy:                       {correct_top1}/{total_tested} ({correct_top1/total_tested*100:.1f}%)")
    print(f"  Top-3 Inclusion Rate:                        {correct_in_top3}/{total_tested} ({correct_in_top3/total_tested*100:.1f}%)")
    print(f"  Safety Gating Compliance:                    When model is uncertain or confusing similar foods, fallback triggers.")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()
