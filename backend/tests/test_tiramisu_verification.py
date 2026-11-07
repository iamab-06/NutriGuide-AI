import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.services.classifier import FoodClassifier

def test():
    clf = FoodClassifier()
    print("Num classes:", clf.num_classes)

    img_path = r"C:\Users\abhij\.gemini\antigravity\brain\bd348a6d-253f-4d7d-a9c4-c0e81c72a89f\.user_uploaded\media_1794032194304_6ba6b98c.jpg"
    with open(img_path, "rb") as f:
        img_bytes = f.read()

    res = clf.predict(img_bytes)
    print("\n--- PREDICTION RESULT ---")
    print("Predicted Class:", res["predicted_class"])
    print("Display Name:   ", res["display_name"])
    print("Confidence:     ", res["confidence"])
    print("Is Confident:   ", res["is_confident"])
    print("\nTop 5 Candidates:")
    for p in res["top_predictions"]:
        print(f"  {p['display_name']}: {p['confidence_pct']}")

if __name__ == "__main__":
    test()
