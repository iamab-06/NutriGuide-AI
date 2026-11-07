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
    """MobileNetV3-Large fine-tuned for NutriGuide food categories (supports 20 or 101 classes)."""

    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model: Optional[nn.Module] = None
        self.categories = SUPPORTED_CATEGORIES
        self.display_names = CATEGORY_DISPLAY_NAMES
        self.num_classes = NUM_CLASSES
        self._load_model()

    def _build_model(self, num_classes: int) -> nn.Module:
        model = models.mobilenet_v3_large(weights=models.MobileNet_V3_Large_Weights.IMAGENET1K_V2)
        in_features = model.classifier[3].in_features
        model.classifier[3] = nn.Linear(in_features, num_classes)
        return model

    def _load_model(self):
        """Load model weights. Automatically selects 101-class model if present, else 20-class model."""
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        f101_weights = os.path.join(backend_dir, "models", "nutriguide_food101_classifier.pth")
        default_weights = settings.model_weights_path
        if not os.path.exists(default_weights):
            candidate = os.path.join(backend_dir, default_weights)
            if os.path.exists(candidate):
                default_weights = candidate

        # Check for 101-class model first
        weights_path = f101_weights if os.path.exists(f101_weights) else default_weights

        if os.path.exists(weights_path):
            try:
                state_dict = torch.load(weights_path, map_location=self.device, weights_only=True)
                head_weight = state_dict.get("classifier.3.weight")
                if head_weight is not None and head_weight.shape[0] == 101:
                    self.num_classes = 101
                    f101_classes_path = os.path.join(backend_dir, "models", "food101_classes.json")
                    if os.path.exists(f101_classes_path):
                        with open(f101_classes_path, "r", encoding="utf-8") as f:
                            self.categories = json.load(f)
                    else:
                        self.categories = sorted(ALL_FOOD101_CATEGORIES)
                    self.display_names = {cat: cat.replace("_", " ").title() for cat in self.categories}
                    logger.info(f"Detected 101-class checkpoint with {self.num_classes} categories.")
                else:
                    self.num_classes = 20
                    self.categories = SUPPORTED_CATEGORIES
                    self.display_names = CATEGORY_DISPLAY_NAMES

                self.model = self._build_model(self.num_classes)
                self.model.load_state_dict(state_dict)
                logger.info(f"Loaded fine-tuned weights ({self.num_classes} classes) from {weights_path}")
            except Exception as e:
                logger.warning(f"Could not load weights from {weights_path}: {e}. Using pretrained backbone.")
                self.model = self._build_model(self.num_classes)
        else:
            self.model = self._build_model(self.num_classes)
            logger.info("No fine-tuned weights found. Using ImageNet pretrained backbone.")

        self.model.to(self.device)
        self.model.eval()

    def predict(self, image_bytes: bytes) -> Dict[str, Any]:
        """Classify food image. Returns prediction with confidence scores."""
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

        with torch.no_grad():
            logits = self.model(tensor)
            probs = torch.softmax(logits, dim=1)[0]

        top_k = min(5, self.num_classes)
        top_probs, top_indices = torch.topk(probs, top_k)

        predictions = []
        for prob, idx in zip(top_probs.cpu().numpy(), top_indices.cpu().numpy()):
            cat = self.categories[int(idx)]
            disp = self.display_names.get(cat, cat.replace("_", " ").title())
            predictions.append({
                "class": cat,
                "display_name": disp,
                "confidence": float(prob),
                "confidence_pct": f"{float(prob)*100:.1f}%",
            })

        top = predictions[0]
        is_confident = top["confidence"] >= CONFIDENCE_THRESHOLD

        return {
            "predicted_class": top["class"],
            "display_name": top["display_name"],
            "confidence": top["confidence"],
            "top_predictions": predictions,
            "is_confident": is_confident,
            "confidence_threshold": CONFIDENCE_THRESHOLD,
            "model_version": f"MobileNetV3-NutriGuide-v{'101' if self.num_classes == 101 else '1'}",
            "supported_categories": list(self.display_names.values()),
        }


# Module-level singleton
_classifier: Optional[FoodClassifier] = None


def get_classifier() -> FoodClassifier:
    global _classifier
    if _classifier is None:
        _classifier = FoodClassifier()
    return _classifier
