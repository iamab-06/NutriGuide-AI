"""
NutriGuide AI - Dataset Extractor for 20 Food Categories
Extracts Food-101 official train and validation sets for the 20 NutriGuide categories.
Saves standard ImageFolder structure:
  backend/datasets/food20/
    train/<category>/...
    val/<category>/...
"""
import glob
import io
import json
import logging
import os
from pathlib import Path

import polars as pl
from PIL import Image
from huggingface_hub import hf_hub_download

from app.core.categories import SUPPORTED_CATEGORIES

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("prepare_food20")

DEST_DIR = Path("datasets/food20")
TRAIN_DIR = DEST_DIR / "train"
VAL_DIR = DEST_DIR / "val"


def get_class_mappings():
    names = json.load(open("food101_names.json"))
    rev = {v: int(k) for k, v in names.items()}
    f101_to_cat = {rev[cat]: cat for cat in SUPPORTED_CATEGORIES}
    return f101_to_cat


def extract_from_parquet(parquet_path: str, output_base: Path, f101_to_cat: dict, max_per_class: int = None):
    target_labels = list(f101_to_cat.keys())
    df = pl.scan_parquet(parquet_path).filter(pl.col("label").is_in(target_labels)).collect()
    
    counts = {cat: 0 for cat in SUPPORTED_CATEGORIES}
    extracted = 0

    for row in df.iter_rows(named=True):
        f101_lbl = row["label"]
        cat_name = f101_to_cat[f101_lbl]
        
        target_dir = output_base / cat_name
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Unique filename using class and count
        existing_count = len(os.listdir(target_dir))
        if max_per_class and existing_count >= max_per_class:
            continue
            
        img_bytes = row["image"]["bytes"]
        img_path = target_dir / f"{cat_name}_{existing_count:05d}.jpg"
        
        with open(img_path, "wb") as f:
            f.write(img_bytes)
            
        extracted += 1
        counts[cat_name] += 1

    return extracted, counts


def prepare_validation(f101_to_cat: dict):
    logger.info("Extracting validation / test images from local cache...")
    val_files = sorted(glob.glob(
        r"C:\Users\abhij\.cache\huggingface\hub\datasets--ethz--food101\**\validation-*.parquet",
        recursive=True
    ))
    total_val = 0
    for vf in val_files:
        logger.info(f"Processing validation shard: {os.path.basename(vf)}")
        extracted, _ = extract_from_parquet(vf, VAL_DIR, f101_to_cat)
        total_val += extracted
    logger.info(f"Total validation images extracted: {total_val}")


def prepare_training(f101_to_cat: dict, num_shards: int = 8):
    logger.info(f"Downloading and extracting {num_shards} training shards...")
    total_train = 0
    for shard_idx in range(num_shards):
        shard_name = f"data/train-{shard_idx:05d}-of-00008.parquet"
        logger.info(f"Downloading training shard [{shard_idx+1}/{num_shards}]: {shard_name}...")
        parquet_path = hf_hub_download("ethz/food101", shard_name, repo_type="dataset")
        extracted, _ = extract_from_parquet(parquet_path, TRAIN_DIR, f101_to_cat)
        total_train += extracted
        logger.info(f"Shard {shard_idx} complete: extracted {extracted} images (total train so far: {total_train})")
    logger.info(f"Total training images extracted: {total_train}")


def main():
    f101_to_cat = get_class_mappings()
    
    # Extract validation
    prepare_validation(f101_to_cat)
    
    # Extract train (all 8 shards for full 15,000 images)
    prepare_training(f101_to_cat, num_shards=8)
    
    logger.info("Dataset preparation complete!")


if __name__ == "__main__":
    main()
