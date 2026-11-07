"""
NutriGuide AI - Classifier Evaluation Script
Evaluates food classifier on the official Food-101 test/validation split (5,000 images across 20 classes).
Measures:
- Top-1 and Top-3 accuracy
- Per-class accuracy and precision/recall
- Confusion matrix
- Classification latency (mean, median, p95)
"""
import glob
import io
import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import polars as pl
import torch
from PIL import Image
from sklearn.metrics import classification_report, confusion_matrix

from app.core.categories import SUPPORTED_CATEGORIES, CATEGORY_DISPLAY_NAMES, NUM_CLASSES
from app.services.classifier import FoodClassifier, PREPROCESS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("evaluate_classifier")


def load_test_dataset(max_per_class: int = None) -> List[Tuple[bytes, int, str]]:
    """
    Extract test images from downloaded Food-101 validation parquet files.
    Returns: list of (image_bytes, target_class_idx_0_to_19, category_name)
    """
    names = json.load(open("food101_names.json"))
    rev = {v: int(k) for k, v in names.items()}
    
    # Map Food-101 original label ID -> NutriGuide 0-19 index
    f101_to_nutri = {rev[cat]: idx for idx, cat in enumerate(SUPPORTED_CATEGORIES)}
    target_f101_labels = list(f101_to_nutri.keys())
    
    files = glob.glob(
        r"C:\Users\abhij\.cache\huggingface\hub\datasets--ethz--food101\**\validation-*.parquet",
        recursive=True
    )
    if not files:
        raise FileNotFoundError("No Food-101 validation parquet files found in cache.")

    logger.info(f"Loading test samples from {len(files)} parquet files...")
    samples_per_class = {idx: 0 for idx in range(NUM_CLASSES)}
    test_data = []

    for f in sorted(files):
        df = pl.scan_parquet(f).filter(pl.col("label").is_in(target_f101_labels)).collect()
        for row in df.iter_rows(named=True):
            f101_lbl = row["label"]
            nutri_idx = f101_to_nutri[f101_lbl]
            if max_per_class and samples_per_class[nutri_idx] >= max_per_class:
                continue
            
            img_bytes = row["image"]["bytes"]
            cat_name = SUPPORTED_CATEGORIES[nutri_idx]
            test_data.append((img_bytes, nutri_idx, cat_name))
            samples_per_class[nutri_idx] += 1

    logger.info(f"Loaded {len(test_data)} test samples across {NUM_CLASSES} classes.")
    return test_data


def evaluate_classifier(max_per_class: int = 50, output_file: str = "models/eval_results.json"):
    """
    Run full evaluation on FoodClassifier.
    max_per_class: default 50 (1,000 test images for fast evaluation) or None for all 5,000.
    """
    classifier = FoodClassifier()
    test_data = load_test_dataset(max_per_class=max_per_class)
    
    y_true = []
    y_pred = []
    y_top3 = []
    latencies_ms = []

    logger.info(f"Evaluating {len(test_data)} images on {classifier.device}...")
    start_eval = time.time()

    for idx, (img_bytes, label_idx, cat_name) in enumerate(test_data):
        t0 = time.perf_counter()
        pred = classifier.predict(img_bytes)
        lat_ms = (time.perf_counter() - t0) * 1000.0
        latencies_ms.append(lat_ms)

        predicted_cat = pred["predicted_class"]
        pred_idx = SUPPORTED_CATEGORIES.index(predicted_cat)
        top3_cats = [p["class"] for p in pred["top_predictions"][:3]]
        top3_indices = [SUPPORTED_CATEGORIES.index(c) for c in top3_cats]

        y_true.append(label_idx)
        y_pred.append(pred_idx)
        y_top3.append(top3_indices)

        if (idx + 1) % 200 == 0:
            current_top1 = 100.0 * sum(1 for yt, yp in zip(y_true, y_pred) if yt == yp) / len(y_true)
            logger.info(f"Progress: [{idx+1}/{len(test_data)}] Current Top-1 Acc: {current_top1:.2f}%")

    total_time = time.time() - start_eval

    # Metrics
    y_true_arr = np.array(y_true)
    y_pred_arr = np.array(y_pred)
    
    top1_correct = (y_true_arr == y_pred_arr).sum()
    top1_acc = 100.0 * top1_correct / len(y_true)
    
    top3_correct = sum(1 for yt, top3 in zip(y_true, y_top3) if yt in top3)
    top3_acc = 100.0 * top3_correct / len(y_true)

    # Per-class accuracy
    per_class = {}
    for i, cat in enumerate(SUPPORTED_CATEGORIES):
        mask = (y_true_arr == i)
        total_c = int(mask.sum())
        correct_c = int((y_pred_arr[mask] == i).sum()) if total_c > 0 else 0
        acc_c = (100.0 * correct_c / total_c) if total_c > 0 else 0.0
        per_class[cat] = {
            "display_name": CATEGORY_DISPLAY_NAMES[cat],
            "correct": correct_c,
            "total": total_c,
            "accuracy_pct": round(acc_c, 2)
        }

    # Confusion Matrix
    cm = confusion_matrix(y_true_arr, y_pred_arr, labels=list(range(NUM_CLASSES))).tolist()

    # Latency Stats
    lat_mean = float(np.mean(latencies_ms))
    lat_median = float(np.median(latencies_ms))
    lat_p95 = float(np.percentile(latencies_ms, 95))

    results = {
        "model_version": "MobileNetV3-NutriGuide-v1",
        "device": str(classifier.device),
        "total_test_images": len(y_true),
        "top1_accuracy_pct": round(top1_acc, 2),
        "top3_accuracy_pct": round(top3_acc, 2),
        "latency_ms": {
            "mean": round(lat_mean, 2),
            "median": round(lat_median, 2),
            "p95": round(lat_p95, 2),
        },
        "per_class": per_class,
        "confusion_matrix": cm,
        "evaluation_time_sec": round(total_time, 2)
    }

    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    logger.info("=" * 60)
    logger.info(f"EVALUATION RESULTS ({len(y_true)} test images)")
    logger.info(f"Top-1 Accuracy : {top1_acc:.2f}%")
    logger.info(f"Top-3 Accuracy : {top3_acc:.2f}%")
    logger.info(f"Latency Mean   : {lat_mean:.2f} ms (p95: {lat_p95:.2f} ms)")
    logger.info(f"Results saved to: {output_file}")
    logger.info("=" * 60)

    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-per-class", type=int, default=50, help="Max test images per class (None for all 250)")
    parser.add_argument("--out", type=str, default="models/eval_results.json")
    args = parser.parse_args()
    evaluate_classifier(max_per_class=args.max_per_class, output_file=args.out)
