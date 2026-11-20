"""
NutriGuide AI - Concurrent Image Collector for Karnataka Foods
Uses ThreadPoolExecutor to download authentic dish images in parallel.
"""
import io
import time
import logging
from pathlib import Path
from typing import List, Dict, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from PIL import Image

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("karnataka_fast_collect")

BASE_DIR = Path(__file__).resolve().parent
DATASET_DIR = BASE_DIR / "datasets" / "karnataka15"
TRAIN_DIR = DATASET_DIR / "train"
VAL_DIR = DATASET_DIR / "val"

DISH_QUERIES: Dict[str, List[str]] = {
    "akki_rotti": ["akki rotti", "akki roti", "rice rotti"],
    "bisi_bele_bath": ["bisi bele bath", "bisibelebath"],
    "chitranna": ["chitranna", "lemon rice south india"],
    "dharwad_peda": ["dharwad peda", "dharwad pedha"],
    "donne_biryani": ["donne biryani", "biryani leaf"],
    "holige_obbattu": ["holige", "obbattu", "puran poli"],
    "jolada_rotti": ["jolada rotti", "jowar roti"],
    "karnataka_sambar": ["sambar dish", "udupi sambar"],
    "kesari_bath": ["kesari bath", "rava kesari"],
    "maddur_vada": ["maddur vada", "maddur vade"],
    "mangalore_buns": ["mangalore buns", "mangaluru buns"],
    "mysore_pak": ["mysore pak", "mysur pak"],
    "neer_dosa": ["neer dosa", "neer dose"],
    "ragi_mudde": ["ragi mudde", "ragi ball"],
    "rava_idli": ["rava idli", "rave idli"],
}

HEADERS = {"User-Agent": "NutriGuideResearch/1.0 (academic; student@project.edu)"}


def download_single_image(url: str, min_size: int = 120) -> Image.Image:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=5)
        if resp.status_code != 200:
            return None
        img = Image.open(io.BytesIO(resp.content)).convert("RGB")
        w, h = img.size
        if w < min_size or h < min_size:
            return None
        if max(w, h) / min(w, h) > 3.0:
            return None
        return img
    except Exception:
        return None


def fetch_wikimedia_thumb_urls(search_query: str, limit: int = 20) -> List[str]:
    api_url = "https://commons.wikimedia.org/w/api.php"
    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": search_query,
        "gsrnamespace": 6,
        "gsrlimit": limit,
        "prop": "imageinfo",
        "iiprop": "url",
        "iiurlwidth": 512,
        "format": "json",
    }
    try:
        r = requests.get(api_url, params=params, headers=HEADERS, timeout=6)
        if r.status_code != 200:
            return []
        data = r.json()
        pages = data.get("query", {}).get("pages", {})
        urls = []
        for pid, p in pages.items():
            ii = p.get("imageinfo", [{}])[0]
            thumb = ii.get("thumburl") or ii.get("url")
            if thumb and not any(ext in thumb.lower() for ext in [".svg", ".ogg", ".webm", ".pdf"]):
                urls.append(thumb)
        return urls
    except Exception as e:
        logger.warning(f"Error querying '{search_query}': {e}")
        return []


def collect_dish(dish_id: str, queries: List[str]):
    train_dish_dir = TRAIN_DIR / dish_id
    val_dish_dir = VAL_DIR / dish_id
    train_dish_dir.mkdir(parents=True, exist_ok=True)
    val_dish_dir.mkdir(parents=True, exist_ok=True)

    urls_to_download = []
    seen = set()
    for q in queries:
        found = fetch_wikimedia_thumb_urls(q, limit=18)
        for u in found:
            if u not in seen:
                seen.add(u)
                urls_to_download.append(u)

    print(f"[{dish_id}] Found {len(urls_to_download)} candidate URLs. Downloading in parallel...", flush=True)

    valid_images = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_url = {executor.submit(download_single_image, u): u for u in urls_to_download}
        for future in as_completed(future_to_url):
            img = future.result()
            if img:
                valid_images.append(img)

    print(f"[{dish_id}] Successfully downloaded {len(valid_images)} valid images.", flush=True)
    if not valid_images:
        return

    # Split: 20% val (at least 2), rest train
    val_count = max(2, int(len(valid_images) * 0.2))
    val_imgs = valid_images[:val_count]
    train_imgs = valid_images[val_count:]

    for idx, img in enumerate(train_imgs, 1):
        p = train_dish_dir / f"{dish_id}_train_{idx:03d}.jpg"
        img.save(p, "JPEG", quality=90)

    for idx, img in enumerate(val_imgs, 1):
        p = val_dish_dir / f"{dish_id}_val_{idx:03d}.jpg"
        img.save(p, "JPEG", quality=90)

    print(f"[{dish_id}] Saved: {len(train_imgs)} train, {len(val_imgs)} val.", flush=True)


def main():
    print("=== STARTING PARALLEL DATASET COLLECTION ===", flush=True)
    t0 = time.time()
    for dish_id, queries in DISH_QUERIES.items():
        collect_dish(dish_id, queries)
    print(f"=== COMPLETED IN {round(time.time() - t0, 1)}s ===", flush=True)


if __name__ == "__main__":
    main()
