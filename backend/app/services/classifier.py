"""
NutriGuide AI - Food Image Classifier
Uses MobileNetV3-Large pretrained on ImageNet, with custom head for food categories.
"""
import io
import json
import logging
import os
from typing import List, Dict, Any, Optional, Tuple

import torch
import torch.nn as nn
import torchvision.transforms as transforms
from torchvision import models
from PIL import Image, UnidentifiedImageError

from app.core.categories import (
    SUPPORTED_CATEGORIES,
    CATEGORY_DISPLAY_NAMES,
    NUM_CLASSES,
    ALL_FOOD101_CATEGORIES,
    FOOD101_DISPLAY_NAMES,
)
from app.core.config import settings

logger = logging.getLogger(__name__)

CONFIDENCE_THRESHOLD = getattr(settings, "confidence_threshold", 0.70)

# ImageNet normalization
PREPROCESS = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    ),
])


class FoodClassifier:
    """
    Dual-Expert MobileNetV3-Large Food Classifier for NutriGuide AI.
    Concurrently runs:
      1. Global Expert: 101 Food-101 categories (Sushi, Pizza, Frozen Yogurt, Ice Cream, etc.)
      2. Regional Expert: 18 Karnataka regional categories (Ragi Mudde, Jowar Roti, Kesari Bath, etc.)
    Dynamically routes predictions in < 50ms on CPU, giving seamless recognition
    across all 118 global and regional food items.
    """

    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.regional_model: Optional[nn.Module] = None
        self.regional_classes: List[str] = []
        self.global_model: Optional[nn.Module] = None
        self.global_classes: List[str] = []
        self.model: Optional[nn.Module] = None
        self.categories: List[str] = list(SUPPORTED_CATEGORIES)
        self.display_names: Dict[str, str] = dict(CATEGORY_DISPLAY_NAMES)
        self.num_classes: int = NUM_CLASSES
        self._load_dual_experts()

    def _build_model(self, num_classes: int) -> nn.Module:
        model = models.mobilenet_v3_large(weights=models.MobileNet_V3_Large_Weights.IMAGENET1K_V2)
        in_features = model.classifier[3].in_features
        model.classifier[3] = nn.Linear(in_features, num_classes)
        return model

    def _load_dual_experts(self):
        """Loads both Regional Karnataka and Global Food-101 models."""
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        models_dir = os.path.join(backend_dir, "models")

        # 1. Load Regional Expert (18 classes)
        reg_weights = os.path.join(models_dir, "nutriguide_classifier.pth")
        reg_classes_path = os.path.join(models_dir, "food35_classes.json")
        if os.path.exists(reg_weights) and os.path.exists(reg_classes_path):
            try:
                with open(reg_classes_path, "r", encoding="utf-8") as f:
                    self.regional_classes = json.load(f)
                num_reg = len(self.regional_classes)
                self.regional_model = self._build_model(num_reg)
                state = torch.load(reg_weights, map_location=self.device, weights_only=True)
                self.regional_model.load_state_dict(state)
                self.regional_model.to(self.device)
                self.regional_model.eval()
                logger.info(f"Loaded Regional Expert ({num_reg} classes) from {reg_weights}")
            except Exception as e:
                logger.warning(f"Could not load Regional Expert: {e}")
                self.regional_model = None

        # 2. Load Global Expert (101 classes)
        f101_weights = os.path.join(models_dir, "nutriguide_food101_classifier.pth")
        f101_classes_path = os.path.join(models_dir, "food101_classes.json")
        if os.path.exists(f101_weights):
            try:
                if os.path.exists(f101_classes_path):
                    with open(f101_classes_path, "r", encoding="utf-8") as f:
                        self.global_classes = json.load(f)
                else:
                    self.global_classes = sorted(ALL_FOOD101_CATEGORIES)
                num_glob = len(self.global_classes)
                self.global_model = self._build_model(num_glob)
                state = torch.load(f101_weights, map_location=self.device, weights_only=True)
                self.global_model.load_state_dict(state)
                self.global_model.to(self.device)
                self.global_model.eval()
                logger.info(f"Loaded Global Expert ({num_glob} classes) from {f101_weights}")
            except Exception as e:
                logger.warning(f"Could not load Global Expert: {e}")
                self.global_model = None

        # Merge categories & display names across both experts
        combined_cats = list(dict.fromkeys(self.regional_classes + self.global_classes))
        if combined_cats:
            self.categories = combined_cats
            self.num_classes = len(combined_cats)

        self.display_names = {}
        for c in self.categories:
            disp = (
                CATEGORY_DISPLAY_NAMES.get(c)
                or FOOD101_DISPLAY_NAMES.get(c)
                or c.replace("_", " ").title()
            )
            self.display_names[c] = disp

        # Single model pointer for legacy callers
        self.model = self.regional_model or self.global_model or self._build_model(self.num_classes)
        self.model.to(self.device)
        self.model.eval()

    def predict(self, image_bytes: bytes) -> Dict[str, Any]:
        """Classify food image using Dual-Expert ensemble."""
        ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP", "GIF"}
        MAX_DIMENSION = 4096

        try:
            raw_img = Image.open(io.BytesIO(image_bytes))
            fmt = (raw_img.format or "").upper()
            if fmt not in ALLOWED_FORMATS:
                raise ValueError(
                    f"Unsupported image format: {fmt or 'Unknown'}. Allowed: JPEG, PNG, WebP, GIF."
                )

            width, height = raw_img.size
            if width > MAX_DIMENSION or height > MAX_DIMENSION:
                raise ValueError(
                    f"Image dimensions ({width}x{height}) exceed maximum allowed limit of {MAX_DIMENSION}x{MAX_DIMENSION}."
                )

            image = raw_img.convert("RGB")
        except Image.DecompressionBombError:
            raise ValueError("Cannot open image: Image exceeds maximum decompression safety limits.")
        except (UnidentifiedImageError, OSError):
            raise ValueError("Cannot open image: Invalid image file or unsupported image format.")
        except ValueError:
            raise
        except Exception:
            raise ValueError("Failed to process image payload.")

        tensor = PREPROCESS(image).unsqueeze(0).to(self.device)

        reg_preds = []
        glob_preds = []
        score_r = 0.0
        score_g = 0.0

        with torch.no_grad():
            if self.regional_model and self.regional_classes:
                logits_r = self.regional_model(tensor)
                probs_r = torch.softmax(logits_r, dim=1)[0]
                val_r, idx_r = torch.sort(probs_r, descending=True)
                top_r_prob = val_r[0].item()
                top_r_margin = (val_r[0] - val_r[1]).item() if len(val_r) > 1 else top_r_prob
                score_r = top_r_prob * (0.5 + top_r_margin)

                for p, i in zip(val_r[:5].cpu().numpy(), idx_r[:5].cpu().numpy()):
                    c = self.regional_classes[int(i)]
                    reg_preds.append({
                        "class": c,
                        "display_name": self.display_names.get(c, c.replace("_", " ").title()),
                        "confidence": float(p),
                        "confidence_pct": f"{float(p)*100:.1f}%",
                    })

            if self.global_model and self.global_classes:
                logits_g = self.global_model(tensor)
                probs_g = torch.softmax(logits_g, dim=1)[0]
                val_g, idx_g = torch.sort(probs_g, descending=True)
                top_g_prob = val_g[0].item()
                top_g_margin = (val_g[0] - val_g[1]).item() if len(val_g) > 1 else top_g_prob
                score_g = top_g_prob * (0.5 + top_g_margin)

                for p, i in zip(val_g[:5].cpu().numpy(), idx_g[:5].cpu().numpy()):
                    c = self.global_classes[int(i)]
                    glob_preds.append({
                        "class": c,
                        "display_name": self.display_names.get(c, c.replace("_", " ").title()),
                        "confidence": float(p),
                        "confidence_pct": f"{float(p)*100:.1f}%",
                    })

        # Decision routing based on margin-calibrated certainty
        if score_g > score_r and glob_preds:
            primary_list = glob_preds
            secondary_list = reg_preds
            expert_name = "Global Food-101"
        elif reg_preds:
            primary_list = reg_preds
            secondary_list = glob_preds
            expert_name = "Regional Karnataka"
        else:
            primary_list = glob_preds
            secondary_list = []
            expert_name = "Standard"

        # Combine top predictions without duplicates
        combined_predictions = []
        seen = set()
        for p in primary_list + secondary_list:
            if p["class"] not in seen:
                seen.add(p["class"])
                combined_predictions.append(p)
            if len(combined_predictions) >= 5:
                break

        top = combined_predictions[0]
        is_confident = top["confidence"] >= CONFIDENCE_THRESHOLD

        return {
            "predicted_class": top["class"],
            "display_name": top["display_name"],
            "confidence": top["confidence"],
            "top_predictions": combined_predictions,
            "is_confident": is_confident,
            "confidence_threshold": CONFIDENCE_THRESHOLD,
            "model_version": f"MobileNetV3-DualExpert ({self.num_classes} categories)",
            "supported_categories": list(self.display_names.values()),
        }


# Module-level singleton
_classifier: Optional[FoodClassifier] = None


def get_classifier() -> FoodClassifier:
    global _classifier
    if _classifier is None:
        _classifier = FoodClassifier()
    return _classifier
