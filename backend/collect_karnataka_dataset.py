"""
NutriGuide AI - Karnataka Food Dataset Collector
Collects authentic images for the 15 Karnataka regional food categories.
Saves to backend/datasets/karnataka15/train and backend/datasets/karnataka15/val.
"""
import io
import os
import time
import logging
from pathlib import Path
from typing import List, Tuple
import requests
from PIL import Image
from ddgs import DDGS

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("collect_karnataka")

BASE_DIR = Path(__file__).resolve().parent
DATASET_DIR = BASE_DIR / "datasets" / "karnataka15"
TRAIN_DIR = DATASET_DIR / "train"
VAL_DIR = DATASET_DIR / "val"

KARNATAKA_DISHES = [
    ("akki_rotti", ["akki rotti karnataka food", "akki roti recipe dish", "spiced rice flour rotti karnataka"]),
    ("bisi_bele_bath", ["bisi bele bath karnataka food", "authentic bisibelebath rice", "bisi bele bhat recipe"]),
    ("chitranna", ["chitranna karnataka lemon rice", "chitranna rice dish", "tempered lemon rice karnataka"]),
    ("dharwad_peda", ["dharwad peda sweet karnataka", "authentic dharwad pedha", "dharwad peda babu singh"]),
    ("donne_biryani", ["bangalore donne biryani chicken", "donne biryani karnataka", "military hotel donne biryani"]),
    ("holige_obbattu", ["holige karnataka sweet", "obbattu bele holige sweet", "puran poli holige karnataka"]),
    ("jolada_rotti", ["jolada rotti north karnataka", "jowar roti karnataka food", "jolada rotti with yennegai"]),
    ("karnataka_sambar", ["karnataka udupi sambar", "mysore sambar coconut jaggery", "karnataka style sambar dish"]),
    ("kesari_bath", ["kesari bath karnataka sweet", "rava kesari halwa karnataka", "chow chow bath kesari"]),
    ("maddur_vada", ["maddur vada karnataka snack", "crispy maddur vada recipe", "maddur vade karnataka"]),
    ("mangalore_buns", ["mangalore buns sweet banana puri", "mangaluru buns karnataka", "udupi mangalore buns"]),
    ("mysore_pak", ["mysore pak sweet karnataka", "ghee mysore pak sweet", "authentic mysore pak"]),
    ("neer_dosa", ["neer dosa coastal karnataka", "neer dose mangalore", "soft lacy neer dosa"]),
    ("ragi_mudde", ["ragi mudde karnataka food", "ragi ball finger millet mudde", "steamed ragi mudde"]),
    ("rava_idli", ["rava idli karnataka mtr", "steamed sooji rava idli", "karnataka rava idli recipe"]),
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def download_and_verify_image(url: str, min_size: int = 150) -> Image.Image:
    """Download image and verify it is a valid RGB image."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=8)
        if resp.status_code != 200:
            return None
        img = Image.open(io.BytesIO(resp.content))
        img = img.convert("RGB")
        w, h = img.size
        if w < min_size or h < min_size:
            return None
        # Check aspect ratio (ignore ultra-wide banners or long strips)
        aspect = max(w, h) / min(w, h)
        if aspect > 2.5:
            return None
        return img
    except Exception:
        return None


def collect_dish_images(dish_id: str, search_queries: List[str], target_train: int = 25, target_val: int = 5):
    train_dish_dir = TRAIN_DIR / dish_id
    val_dish_dir = VAL_DIR / dish_id
    train_dish_dir.mkdir(parents=True, exist_ok=True)
    val_dish_dir.mkdir(parents=True, exist_ok=True)

    # Check if images already exist
    existing_train = len(list(train_dish_dir.glob("*.jpg")))
    existing_val = len(list(val_dish_dir.glob("*.jpg")))
    if existing_train >= target_train and existing_val >= target_val:
        logger.info(f"[{dish_id}] Already has {existing_train} train and {existing_val} val images. Skipping.")
        return

    logger.info(f"[{dish_id}] Collecting images (Target: {target_train} train, {target_val} val)...")
    downloaded_urls = set()
    saved_count = existing_train + existing_val
    needed = (target_train + target_val) - saved_count

    with DDGS() as ddgs:
        for q in search_queries:
            if needed <= 0:
                break
            try:
                results = list(ddgs.images(q, max_results=35))
                time.sleep(1)
            except Exception as e:
                logger.warning(f"Error querying '{q}': {e}")
                time.sleep(2)
                continue

            for r in results:
                if needed <= 0:
                    break
                img_url = r.get("image")
                if not img_url or img_url in downloaded_urls:
                    continue
                downloaded_urls.add(img_url)

                img = download_and_verify_image(img_url)
                if img is None:
                    continue

                saved_count += 1
                needed -= 1

                # Save to val if val is not full, else train
                current_val = len(list(val_dish_dir.glob("*.jpg")))
                if current_val < target_val:
                    save_path = val_dish_dir / f"{dish_id}_val_{current_val + 1:03d}.jpg"
                else:
                    current_train = len(list(train_dish_dir.glob("*.jpg")))
                    save_path = train_dish_dir / f"{dish_id}_train_{current_train + 1:03d}.jpg"

                img.save(save_path, "JPEG", quality=90)
                logger.info(f"  Saved {save_path.name} (size: {img.size})")

    final_train = len(list(train_dish_dir.glob("*.jpg")))
    final_val = len(list(val_dish_dir.glob("*.jpg")))
    logger.info(f"[{dish_id}] Done: {final_train} train images, {final_val} val images.")


def main():
    logger.info("Starting Karnataka Food Dataset Collection...")
    for dish_id, queries in KARNATAKA_DISHES:
        collect_dish_images(dish_id, queries, target_train=25, target_val=6)
        time.sleep(1)
    logger.info("Dataset Collection Complete!")


if __name__ == "__main__":
    main()
