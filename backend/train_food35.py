"""
NutriGuide AI - MobileNetV3-Large Classifier Training for 35 Food Categories
Combines 20 Food-101 benchmark categories + 15 Karnataka traditional food categories.
Saves checkpoint to models/nutriguide_classifier.pth and class index to models/food35_classes.json.
"""
import io
import json
import logging
import os
import shutil
import time
from pathlib import Path
from typing import Tuple

import torch
import torch.nn as nn
import torch.optim as optim
from torch.optim.lr_scheduler import CosineAnnealingLR
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("train_food35")

BASE_DIR = Path(__file__).resolve().parent
FOOD20_DIR = BASE_DIR / "datasets" / "food20"
KARNATAKA15_DIR = BASE_DIR / "datasets" / "karnataka15"
FOOD35_DIR = BASE_DIR / "datasets" / "food35"
TRAIN_35 = FOOD35_DIR / "train"
VAL_35 = FOOD35_DIR / "val"
MODELS_DIR = BASE_DIR / "models"
CHECKPOINT_PATH = MODELS_DIR / "nutriguide_classifier.pth"
CLASSES_JSON_PATH = MODELS_DIR / "food35_classes.json"
TRAINING_LOG_PATH = MODELS_DIR / "training_log35.json"


def prepare_food35_dataset():
    """Returns verified classes in datasets/food35."""
    train_classes = sorted([d.name for d in TRAIN_35.iterdir() if d.is_dir()])
    val_classes = sorted([d.name for d in VAL_35.iterdir() if d.is_dir()])
    logger.info(f"Dataset verified: {len(train_classes)} train classes, {len(val_classes)} val classes.")
    return train_classes


def get_dataloaders(batch_size: int = 32):
    train_transform = transforms.Compose([
        transforms.RandomResizedCrop(224, scale=(0.7, 1.0)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(15),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    val_transform = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    train_ds = datasets.ImageFolder(str(TRAIN_35), transform=train_transform)
    val_ds = datasets.ImageFolder(str(VAL_35), transform=val_transform)

    assert train_ds.classes == val_ds.classes, (
        f"Mismatch between train classes ({len(train_ds.classes)}) and val classes ({len(val_ds.classes)})!\n"
        f"Train: {train_ds.classes}\nVal: {val_ds.classes}"
    )

    logger.info(f"Training samples: {len(train_ds)} across {len(train_ds.classes)} classes.")
    logger.info(f"Validation samples: {len(val_ds)} across {len(val_ds.classes)} classes.")

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=0)

    return train_loader, val_loader, train_ds.classes


def build_model(num_classes: int) -> nn.Module:
    logger.info(f"Building MobileNetV3-Large with pretrained ImageNet-1K V2 weights ({num_classes} classes)...")
    model = models.mobilenet_v3_large(weights=models.MobileNet_V3_Large_Weights.IMAGENET1K_V2)
    in_features = model.classifier[3].in_features
    model.classifier[3] = nn.Linear(in_features, num_classes)
    return model


def train_classifier(epochs: int = 8, batch_size: int = 32, lr: float = 1e-3):
    device = torch.device("cpu")
    logger.info(f"Training on device: {device}")

    classes = prepare_food35_dataset()
    num_classes = len(classes)
    train_loader, val_loader, class_names = get_dataloaders(batch_size=batch_size)

    # Save class names JSON
    with open(CLASSES_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(class_names, f, indent=2)
    logger.info(f"Saved class names to {CLASSES_JSON_PATH}")

    model = build_model(num_classes).to(device)

    # Freeze backbone initially, train only classifier head for first 3 epochs
    for name, param in model.named_parameters():
        if "classifier" not in name:
            param.requires_grad = False

    criterion = nn.CrossEntropyLoss(label_smoothing=0.1)
    optimizer = optim.AdamW(filter(lambda p: p.requires_grad, model.parameters()), lr=lr, weight_decay=1e-4)

    best_val_acc = 0.0
    history = []

    logger.info("Phase 1: Training classifier head (backbone frozen)...")
    for epoch in range(1, epochs + 1):
        t0 = time.time()

        # Unfreeze top layers after epoch 3
        if epoch == 4:
            logger.info("Phase 2: Fine-tuning top backbone layers...")
            for name, param in model.named_parameters():
                if "features.15" in name or "features.16" in name or "classifier" in name:
                    param.requires_grad = True
            optimizer = optim.AdamW(filter(lambda p: p.requires_grad, model.parameters()), lr=lr * 0.3, weight_decay=1e-4)

        # Train loop
        model.train()
        train_loss = 0.0
        train_correct = 0
        train_total = 0

        for imgs, labels in train_loader:
            imgs, labels = imgs.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(imgs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            train_loss += loss.item() * imgs.size(0)
            preds = outputs.argmax(dim=1)
            train_correct += (preds == labels).sum().item()
            train_total += imgs.size(0)

        train_acc = train_correct / train_total if train_total > 0 else 0.0
        train_loss = train_loss / train_total if train_total > 0 else 0.0

        # Val loop
        model.eval()
        val_loss = 0.0
        val_correct = 0
        val_total = 0

        with torch.no_grad():
            for imgs, labels in val_loader:
                imgs, labels = imgs.to(device), labels.to(device)
                outputs = model(imgs)
                loss = criterion(outputs, labels)

                val_loss += loss.item() * imgs.size(0)
                preds = outputs.argmax(dim=1)
                val_correct += (preds == labels).sum().item()
                val_total += imgs.size(0)

        val_acc = val_correct / val_total if val_total > 0 else 0.0
        val_loss = val_loss / val_total if val_total > 0 else 0.0
        elapsed = round(time.time() - t0, 1)

        logger.info(
            f"Epoch [{epoch}/{epochs}] ({elapsed}s) - "
            f"Train Loss: {train_loss:.4f}, Train Acc: {train_acc*100:.1f}% | "
            f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc*100:.1f}%"
        )

        history.append({
            "epoch": epoch,
            "train_loss": round(train_loss, 4),
            "train_acc": round(train_acc * 100, 2),
            "val_loss": round(val_loss, 4),
            "val_acc": round(val_acc * 100, 2),
            "time_sec": elapsed,
        })

        # Save best model
        if val_acc >= best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), CHECKPOINT_PATH)
            logger.info(f"Saved new best model checkpoint to {CHECKPOINT_PATH} (Val Acc: {val_acc*100:.1f}%)")

    # Save log
    with open(TRAINING_LOG_PATH, "w", encoding="utf-8") as f:
        json.dump({
            "num_classes": num_classes,
            "classes": class_names,
            "best_val_acc": round(best_val_acc * 100, 2),
            "history": history,
            "trained_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }, f, indent=2)

    logger.info(f"Training completed successfully! Best Validation Accuracy: {best_val_acc*100:.1f}%")
    return model, class_names


if __name__ == "__main__":
    train_classifier(epochs=10, batch_size=32)
