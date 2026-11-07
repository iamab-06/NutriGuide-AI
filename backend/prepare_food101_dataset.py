"""
NutriGuide AI - Dataset Extractor for All 101 Food-101 Categories
Extracts Food-101 official train (750/class) and validation (250/class) splits
from local HuggingFace parquet cache into standard ImageFolder directory:
  backend/datasets/food101/
    train/<category>/...
    val/<category>/...
"""
import glob
import io
import json
import logging
import os
import sys
from pathlib import Path

import polars as pl

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("prepare_food101")

DEST_DIR = Path("datasets/food101")
TRAIN_DIR = DEST_DIR / "train"
VAL_DIR = DEST_DIR / "val"
CACHE_DIR = Path(r"C:\Users\abhij\.cache\huggingface\hub\datasets--ethz--food101")

def get_class_mappings():
    names_path = Path("food101_names.json")
    if not names_path.exists():
        names_path = Path("backend/food101_names.json")
    names = json.load(open(names_path, encoding="utf-8"))
    # names maps "0" -> "apple_pie", "1" -> "baby_back_ribs", ..., "100" -> "waffles"
    f101_to_cat = {int(k): v for k, v in names.items()}
    return f101_to_cat

def extract_from_parquet(parquet_path: str, output_base: Path, f101_to_cat: dict, max_per_class: int = None):
    # Scan and extract all 101 labels
    df = pl.scan_parquet(parquet_path).collect()
    extracted = 0

    for row in df.iter_rows(named=True):
        f101_lbl = row["label"]
        cat_name = f101_to_cat.get(f101_lbl)
        if not cat_name:
            continue

        target_dir = output_base / cat_name
        target_dir.mkdir(parents=True, exist_ok=True)

        existing_count = len(os.listdir(target_dir))
        if max_per_class and existing_count >= max_per_class:
            continue

        img_bytes = row["image"]["bytes"]
        img_path = target_dir / f"{cat_name}_{existing_count:05d}.jpg"

        with open(img_path, "wb") as f:
            f.write(img_bytes)

        extracted += 1

    return extracted

def prepare_validation(f101_to_cat: dict):
    logger.info("Extracting validation set (all 101 classes)...")
    val_files = sorted(glob.glob(str(CACHE_DIR / "**" / "validation-*.parquet"), recursive=True))
    if not val_files:
        raise FileNotFoundError(f"No validation parquet shards found in {CACHE_DIR}")

    total_val = 0
    for vf in val_files:
        logger.info(f"Processing validation shard: {os.path.basename(vf)}")
        extracted = extract_from_parquet(vf, VAL_DIR, f101_to_cat, max_per_class=250)
        total_val += extracted
        logger.info(f"  Extracted {extracted} images (total val: {total_val})")
    logger.info(f"Finished validation: {total_val} images across 101 classes.")

def prepare_training(f101_to_cat: dict):
    logger.info("Extracting training set (all 101 classes)...")
    train_files = sorted(glob.glob(str(CACHE_DIR / "**" / "train-*.parquet"), recursive=True))
    if not train_files:
        raise FileNotFoundError(f"No train parquet shards found in {CACHE_DIR}")

    total_train = 0
    for tf in train_files:
        logger.info(f"Processing training shard: {os.path.basename(tf)}")
        extracted = extract_from_parquet(tf, TRAIN_DIR, f101_to_cat, max_per_class=750)
        total_train += extracted
        logger.info(f"  Extracted {extracted} images (total train: {total_train})")
    logger.info(f"Finished training: {total_train} images across 101 classes.")

def main():
    f101_to_cat = get_class_mappings()
    logger.info(f"Loaded {len(f101_to_cat)} classes from food101_names.json.")

    VAL_DIR.mkdir(parents=True, exist_ok=True)
    TRAIN_DIR.mkdir(parents=True, exist_ok=True)

    prepare_validation(f101_to_cat)
    prepare_training(f101_to_cat)
    logger.info("Dataset preparation complete for all 101 classes!")

if __name__ == "__main__":
    main()
