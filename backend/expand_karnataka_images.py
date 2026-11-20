"""
NutriGuide AI - Dataset Expander & Augmenter for Karnataka Foods
Ensures every Karnataka food category has 45+ training images with diverse
realistic variations (lighting, rotations, crops, perspective) to maximize classifier confidence.
Also includes the user's uploaded real-world reference samples.
"""
import io
import os
import random
from pathlib import Path
from PIL import Image, ImageEnhance, ImageOps

BASE_DIR = Path(__file__).resolve().parent
TRAIN_35 = BASE_DIR / "datasets" / "food35" / "train"
VAL_35 = BASE_DIR / "datasets" / "food35" / "val"

USER_UPLOADS = Path(r"C:\Users\abhij\.gemini\antigravity\brain\0b07af27-6c39-46bc-bcc7-9dfed4c4ed55\.user_uploaded")


def augment_image(img: Image.Image, variant_idx: int) -> Image.Image:
    """Applies realistic photographic augmentations."""
    w, h = img.size
    img = img.convert("RGB")

    # 1. Flip
    if variant_idx % 2 == 0:
        img = img.transpose(Image.FLIP_LEFT_RIGHT)

    # 2. Slight rotation (-15 to 15 degrees)
    angle = random.uniform(-15, 15)
    img = img.rotate(angle, resample=Image.BICUBIC, expand=False)

    # 3. Brightness variation
    factor_b = random.uniform(0.85, 1.2)
    img = ImageEnhance.Brightness(img).enhance(factor_b)

    # 4. Contrast variation
    factor_c = random.uniform(0.85, 1.25)
    img = ImageEnhance.Contrast(img).enhance(factor_c)

    # 5. Color saturation variation
    factor_s = random.uniform(0.85, 1.3)
    img = ImageEnhance.Color(img).enhance(factor_s)

    # 6. Random crop & zoom (90% to 100%)
    crop_scale = random.uniform(0.88, 0.98)
    cw, ch = int(w * crop_scale), int(h * crop_scale)
    x = random.randint(0, w - cw)
    y = random.randint(0, h - ch)
    img = img.crop((x, y, x + cw, y + ch)).resize((w, h), Image.LANCZOS)

    return img


def add_user_references():
    """Extract and add food regions from user screenshots if present."""
    if not USER_UPLOADS.exists():
        return

    # User references:
    # media_1794743696902_8cba0b21.jpg -> Idli with sambar (rava_idli)
    # media_1794743730998_d2807347.jpg -> Ragi Mudde (ragi_mudde)
    # media_1794743777758_b7e416b0.jpg -> Akki Rotti (akki_rotti)
    ref_map = [
        ("media_1794743696902_8cba0b21.jpg", "rava_idli"),
        ("media_1794743730998_d2807347.jpg", "ragi_mudde"),
        ("media_1794743777758_b7e416b0.jpg", "akki_rotti"),
    ]

    for filename, cat in ref_map:
        file_path = USER_UPLOADS / filename
        if file_path.exists():
            try:
                full_img = Image.open(file_path)
                w, h = full_img.size
                # Food is displayed in the left column: x roughly 50 to 245, y 75 to 630
                food_crop = full_img.crop((55, 75, min(250, w), min(630, h)))
                target_train = TRAIN_35 / cat
                target_val = VAL_35 / cat
                target_train.mkdir(parents=True, exist_ok=True)
                target_val.mkdir(parents=True, exist_ok=True)

                food_crop.save(target_train / f"{cat}_user_ref_01.jpg", "JPEG", quality=95)
                food_crop.save(target_val / f"{cat}_user_ref_val.jpg", "JPEG", quality=95)

                # Add 5 augmented copies of the user sample
                for k in range(5):
                    aug = augment_image(food_crop, k)
                    aug.save(target_train / f"{cat}_user_ref_aug_{k+1:02d}.jpg", "JPEG", quality=92)
                print(f"[User Ref] Successfully added authentic user samples for {cat}!")
            except Exception as e:
                print(f"Error extracting user sample {filename}: {e}")


def expand_dataset(target_train_count: int = 45):
    """Augments existing images so every class has at least target_train_count samples."""
    print("=== EXPANDING AND BALANCING DATASET FOR ALL 35 CLASSES ===")

    for cat_dir in sorted(TRAIN_35.iterdir()):
        if not cat_dir.is_dir():
            continue
        cat_name = cat_dir.name
        existing = [p for p in cat_dir.glob("*.jpg") if "aug_" not in p.name]
        if not existing:
            existing = list(cat_dir.glob("*.jpg"))
        if not existing:
            print(f"[{cat_name}] No images found, skipping.")
            continue

        current_total = len(list(cat_dir.glob("*.jpg")))
        needed = target_train_count - current_total

        if needed <= 0:
            print(f"[{cat_name}] Already has {current_total} images. OK.")
            continue

        print(f"[{cat_name}] Has {current_total} images. Generating {needed} augmented samples...")
        created = 0
        while created < needed:
            src_path = random.choice(existing)
            try:
                src_img = Image.open(src_path)
                aug = augment_image(src_img, created)
                save_path = cat_dir / f"{cat_name}_aug_{created+1:03d}.jpg"
                aug.save(save_path, "JPEG", quality=90)
                created += 1
            except Exception as e:
                print(f"Error augmenting {src_path}: {e}")
                break

        final_count = len(list(cat_dir.glob("*.jpg")))
        print(f"[{cat_name}] Now has {final_count} training images.")


def main():
    add_user_references()
    expand_dataset(target_train_count=45)
    print("=== DATASET EXPANSION COMPLETE ===")


if __name__ == "__main__":
    main()
