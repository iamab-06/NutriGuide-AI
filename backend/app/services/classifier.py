"""
NutriGuide AI - Food Image Classifier
Uses MobileNetV3-Large pretrained on ImageNet, with custom head for food categories.
"""
import io
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
)
from app.core.config import settings

logger = logging.getLogger(__name__)

CONFIDENCE_THRESHOLD = 0.40

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
    """MobileNetV3-Large fine-tuned for NutriGuide food categories."""

    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model: Optional[nn.Module] = None
        self._load_model()

    def _build_model(self) -> nn.Module:
        model = models.mobilenet_v3_large(weights=models.MobileNet_V3_Large_Weights.IMAGENET1K_V2)
        # Replace the classifier head
        in_features = model.classifier[3].in_features
        model.classifier[3] = nn.Linear(in_features, NUM_CLASSES)
        return model

    def _load_model(self):
        """Load model weights. Falls back to ImageNet pretrained head if no fine-tuned weights."""
        self.model = self._build_model()
        weights_path = settings.model_weights_path
        if os.path.exists(weights_path):
            try:
                state_dict = torch.load(weights_path, map_location=self.device)
                self.model.load_state_dict(state_dict)
                logger.info(f"Loaded fine-tuned weights from {weights_path}")
            except Exception as e:
                logger.warning(f"Could not load weights from {weights_path}: {e}. Using pretrained backbone.")
        else:
            logger.info("No fine-tuned weights found. Using ImageNet pretrained backbone only.")
            logger.info("Note: classification accuracy will be reduced without fine-tuning.")
        self.model.to(self.device)
        self.model.eval()

    def predict(self, image_bytes: bytes) -> Dict[str, Any]:
        """Classify food image. Returns prediction with confidence scores."""
        try:
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        except (UnidentifiedImageError, Exception) as e:
            raise ValueError(f"Cannot open image: {e}")

        tensor = PREPROCESS(image).unsqueeze(0).to(self.device)

        with torch.no_grad():
            logits = self.model(tensor)
            probs = torch.softmax(logits, dim=1)[0]

        top_k = min(5, NUM_CLASSES)
        top_probs, top_indices = torch.topk(probs, top_k)

        predictions = []
        for prob, idx in zip(top_probs.cpu().numpy(), top_indices.cpu().numpy()):
            cat = SUPPORTED_CATEGORIES[int(idx)]
            predictions.append({
                "class": cat,
                "display_name": CATEGORY_DISPLAY_NAMES[cat],
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
            "model_version": "MobileNetV3-NutriGuide-v1",
            "supported_categories": list(CATEGORY_DISPLAY_NAMES.values()),
        }


# Module-level singleton
_classifier: Optional[FoodClassifier] = None


def get_classifier() -> FoodClassifier:
    global _classifier
    if _classifier is None:
        _classifier = FoodClassifier()
    return _classifier
