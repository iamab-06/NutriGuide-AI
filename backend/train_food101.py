"""
NutriGuide AI - MobileNetV3-Large 101-Class Classifier Training
Fine-tunes MobileNetV3-Large on the complete 101 Food-101 categories using official train/val split.
Optimized for NVIDIA RTX 3050 (4GB VRAM) using mixed precision (torch.amp) and batch size 32.
Saves best checkpoint to: models/nutriguide_food101_classifier.pth
"""
import argparse
import json
import logging
import time
from pathlib import Path

import torch
import torch.nn as nn
import torch.optim as optim
from torch.amp import GradScaler, autocast
from torch.optim.lr_scheduler import CosineAnnealingLR
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms

from app.core.categories import ALL_FOOD101_CATEGORIES

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("train_food101")

TRAIN_DIR = Path("datasets/food101/train")
VAL_DIR = Path("datasets/food101/val")
MODELS_DIR = Path("models")
CHECKPOINT_PATH = MODELS_DIR / "nutriguide_food101_classifier.pth"
LOG_PATH = MODELS_DIR / "training_food101_log.json"
NUM_CLASSES = 101


def get_dataloaders(batch_size: int = 32, num_workers: int = 2):
    train_transform = transforms.Compose([
        transforms.RandomResizedCrop(224, scale=(0.75, 1.0)),
        transforms.RandomHorizontalFlip(),
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

    train_ds = datasets.ImageFolder(str(TRAIN_DIR), transform=train_transform)
    val_ds = datasets.ImageFolder(str(VAL_DIR), transform=val_transform)

    logger.info(f"Verified {len(train_ds.classes)} classes in train dataset.")
    logger.info(f"Training samples: {len(train_ds)} across {len(train_ds.classes)} classes.")
    logger.info(f"Validation samples: {len(val_ds)} across {len(val_ds.classes)} classes.")

    train_loader = DataLoader(
        train_ds, batch_size=batch_size, shuffle=True,
        num_workers=num_workers, pin_memory=True, persistent_workers=(num_workers > 0)
    )
    val_loader = DataLoader(
        val_ds, batch_size=batch_size, shuffle=False,
        num_workers=num_workers, pin_memory=True, persistent_workers=(num_workers > 0)
    )

    return train_loader, val_loader, train_ds.classes


def build_model(device: torch.device) -> nn.Module:
    logger.info(f"Building MobileNetV3-Large for {NUM_CLASSES} classes with ImageNet-1K V2 weights...")
    model = models.mobilenet_v3_large(weights=models.MobileNet_V3_Large_Weights.IMAGENET1K_V2)
    in_features = model.classifier[3].in_features
    model.classifier[3] = nn.Linear(in_features, NUM_CLASSES)
    return model.to(device)


def set_backbone_trainable(model: nn.Module, trainable: bool):
    for name, param in model.named_parameters():
        if "classifier" not in name:
            param.requires_grad = trainable


def train_epoch(model, loader, criterion, optimizer, scaler, device, epoch):
    model.train()
    total_loss = 0.0
    correct = 0
    total = 0

    for batch_idx, (imgs, targets) in enumerate(loader):
        imgs, targets = imgs.to(device, non_blocking=True), targets.to(device, non_blocking=True)
        optimizer.zero_grad()

        with autocast(device_type="cuda" if device.type == "cuda" else "cpu"):
            outputs = model(imgs)
            loss = criterion(outputs, targets)

        if scaler:
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
        else:
            loss.backward()
            optimizer.step()

        total_loss += loss.item() * imgs.size(0)
        _, preds = outputs.max(1)
        correct += preds.eq(targets).sum().item()
        total += imgs.size(0)

        if (batch_idx + 1) % 100 == 0 or (batch_idx + 1) == len(loader):
            logger.info(
                f"Epoch {epoch:02d} [{batch_idx+1:04d}/{len(loader)}] "
                f"Loss: {total_loss/total:.4f}  Top-1 Acc: {100.*correct/total:.2f}%"
            )

    return total_loss / total, 100.0 * correct / total


@torch.no_grad()
def evaluate(model, loader, criterion, device):
    model.eval()
    total_loss = 0.0
    correct_top1 = 0
    correct_top5 = 0
    total = 0

    for imgs, targets in loader:
        imgs, targets = imgs.to(device, non_blocking=True), targets.to(device, non_blocking=True)

        with autocast(device_type="cuda" if device.type == "cuda" else "cpu"):
            outputs = model(imgs)
            loss = criterion(outputs, targets)

        total_loss += loss.item() * imgs.size(0)
        total += imgs.size(0)

        # Top-1
        _, preds = outputs.max(1)
        correct_top1 += preds.eq(targets).sum().item()

        # Top-5
        _, top5_preds = outputs.topk(5, dim=1)
        correct_top5 += top5_preds.eq(targets.view(-1, 1)).sum().item()

    top1 = 100.0 * correct_top1 / total
    top5 = 100.0 * correct_top5 / total
    return total_loss / total, top1, top5


def train(epochs_head: int = 2, epochs_full: int = 3, batch_size: int = 32, lr: float = 3e-4):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Using device: {device} ({torch.cuda.get_device_name(0) if device.type == 'cuda' else 'CPU'})")

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    train_loader, val_loader, class_names = get_dataloaders(batch_size=batch_size)

    # Save class ordering mapping
    with open(MODELS_DIR / "food101_classes.json", "w", encoding="utf-8") as f:
        json.dump(class_names, f, indent=2)

    model = build_model(device)
    criterion = nn.CrossEntropyLoss(label_smoothing=0.1)
    scaler = GradScaler() if device.type == "cuda" else None

    best_val_top1 = 0.0
    history = []

    # Phase 1: Train classification head only
    logger.info(f"--- Phase 1: Training classifier head ({epochs_head} epochs, lr={lr}) ---")
    set_backbone_trainable(model, False)
    optimizer = optim.AdamW(model.classifier.parameters(), lr=lr, weight_decay=1e-4)

    for epoch in range(1, epochs_head + 1):
        t0 = time.time()
        tr_loss, tr_acc = train_epoch(model, train_loader, criterion, optimizer, scaler, device, epoch)
        val_loss, val_top1, val_top5 = evaluate(model, val_loader, criterion, device)
        dt = time.time() - t0
        logger.info(f"Epoch {epoch:02d} finished in {dt:.1f}s | Val Loss: {val_loss:.4f} | Top-1: {val_top1:.2f}% | Top-5: {val_top5:.2f}%")

        if val_top1 > best_val_top1:
            best_val_top1 = val_top1
            torch.save(model.state_dict(), CHECKPOINT_PATH)
            logger.info(f" Saved new best model ({val_top1:.2f}%) to {CHECKPOINT_PATH}")

    # Phase 2: Fine-tune backbone + head
    logger.info(f"--- Phase 2: Full fine-tuning ({epochs_full} epochs, lr={lr/5}) ---")
    set_backbone_trainable(model, True)
    optimizer = optim.AdamW(model.parameters(), lr=lr / 5, weight_decay=1e-4)
    scheduler = CosineAnnealingLR(optimizer, T_max=epochs_full)

    for epoch in range(epochs_head + 1, epochs_head + epochs_full + 1):
        t0 = time.time()
        tr_loss, tr_acc = train_epoch(model, train_loader, criterion, optimizer, scaler, device, epoch)
        val_loss, val_top1, val_top5 = evaluate(model, val_loader, criterion, device)
        scheduler.step()
        dt = time.time() - t0
        logger.info(f"Epoch {epoch:02d} finished in {dt:.1f}s | Val Loss: {val_loss:.4f} | Top-1: {val_top1:.2f}% | Top-5: {val_top5:.2f}%")

        if val_top1 > best_val_top1:
            best_val_top1 = val_top1
            torch.save(model.state_dict(), CHECKPOINT_PATH)
            logger.info(f" Saved new best model ({val_top1:.2f}%) to {CHECKPOINT_PATH}")

    logger.info(f"Training Complete! Best Val Top-1: {best_val_top1:.2f}% saved to {CHECKPOINT_PATH}")


if __name__ == "__main__":
    train()
