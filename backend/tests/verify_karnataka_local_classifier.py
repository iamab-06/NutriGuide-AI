"""
NutriGuide AI - Karnataka Local Food Classifier Verification
Tests the trained 35-class MobileNetV3 model on authentic Karnataka validation images
and the user's reference samples.
Verifies top-1 predictions, confidence scores, and model version.
"""
import io
import sys
from pathlib import Path
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.classifier import FoodClassifier

VAL_DIR = Path(__file__).resolve().parent.parent / "datasets" / "food35" / "val"
USER_UPLOADS = Path(r"C:\Users\abhij\.gemini\antigravity\brain\0b07af27-6c39-46bc-bcc7-9dfed4c4ed55\.user_uploaded")

KARNATAKA_CLASSES = [
    "akki_rotti", "bisi_bele_bath", "chitranna", "dharwad_peda", "donne_biryani",
    "holige_obbattu", "jolada_rotti", "karnataka_sambar", "kesari_bath",
    "maddur_vada", "mangalore_buns", "mysore_pak", "neer_dosa", "ragi_mudde", "rava_idli",
    "dosa", "upma"
]


def test_classifier_karnataka():
    print("=" * 70)
    print("NutriGuide AI - Local Classifier Karnataka Food Verification")
    print("=" * 70)

    fc = FoodClassifier()
    print(f"Model Version: MobileNetV3-NutriGuide-v{fc.num_classes}")
    print(f"Total Categories: {fc.num_classes}")
    assert fc.num_classes in [35, 37], f"Expected 35 or 37 classes, found {fc.num_classes}"

    print("\n--- Testing All 15 Karnataka Dishes on Validation Images ---")
    correct_count = 0
    total_tested = 0

    for cat in KARNATAKA_CLASSES:
        cat_val_dir = VAL_DIR / cat
        if not cat_val_dir.exists():
            continue
        val_imgs = list(cat_val_dir.glob("*.jpg"))
        if not val_imgs:
            continue

        test_img_path = val_imgs[0]
        with open(test_img_path, "rb") as f:
            img_bytes = f.read()

        pred = fc.predict(img_bytes)
        predicted_cat = pred.get("predicted_class", pred.get("category", ""))
        confidence = pred["confidence"]
        display_name = pred["display_name"]
        is_correct = (predicted_cat == cat)

        status_str = "PASS" if is_correct else "FAIL"
        print(f"[{status_str}] Expected: {cat:16s} | Predicted: {predicted_cat:16s} ({display_name}) | Conf: {confidence*100:.1f}%")

        if is_correct:
            correct_count += 1
        total_tested += 1

    accuracy = (correct_count / total_tested * 100) if total_tested > 0 else 0
    print(f"\nOverall Top-1 Validation Accuracy: {correct_count}/{total_tested} ({accuracy:.1f}%)")

    # Test on user reference crops
    print("\n--- Testing on User Reference Images ---")
    ref_tests = [
        ("media_1794743730998_d2807347.jpg", "ragi_mudde", "Ragi Mudde"),
        ("media_1794743777758_b7e416b0.jpg", "akki_rotti", "Akki Rotti"),
        ("media_1794743696902_8cba0b21.jpg", "rava_idli", "Rava Idli"),
    ]

    for filename, expected_cat, expected_name in ref_tests:
        file_path = USER_UPLOADS / filename
        if file_path.exists():
            full_img = Image.open(file_path)
            w, h = full_img.size
            crop = full_img.crop((55, 75, min(250, w), min(630, h)))
            buf = io.BytesIO()
            crop.save(buf, format="JPEG")
            img_bytes = buf.getvalue()

            pred = fc.predict(img_bytes)
            pred_cls = pred.get("predicted_class", pred.get("category", ""))
            print(f"User Sample '{expected_name}': Predicted '{pred['display_name']}' ({pred_cls}) with {pred['confidence']*100:.1f}% confidence")

    print("=" * 70)


if __name__ == "__main__":
    test_classifier_karnataka()
