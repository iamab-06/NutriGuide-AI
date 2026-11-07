"""
NutriGuide AI - MobileNetV3-Large Food Classifier Training
Fine-tunes MobileNetV3-Large on the 20 Food-101 categories using official train/val split.
Uses mixed precision (torch.amp) on CUDA for high training throughput.
Saves best checkpoint to: models/nutriguide_classifier.pth
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

from app.core.categories import SUPPORTED_CATEGORIES, NUM_CLASSES

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("train_food20")

TRAIN_DIR = Path("datasets/food20/train")
VAL_DIR = Path("datasets/food20/val")
MODELS_DIR = Path("models")
CHECKPOINT_PATH = MODELS_DIR / "nutriguide_classifier.pth"
LOG_PATH = MODELS_DIR / "training_log.json"


def get_dataloaders(batch_size: int = 64, num_workers: int = 4):
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

    # Verify class ordering matches app/core/categories.py
    if train_ds.classes != SUPPORTED_CATEGORIES:
        raise ValueError(
            f"ImageFolder classes do not match SUPPORTED_CATEGORIES.\n"
            f"Found: {train_ds.classes}\nExpected: {SUPPORTED_CATEGORIES}"
        )

    logger.info(f"Verified {len(train_ds.classes)} classes match SUPPORTED_CATEGORIES exactly.")
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

    return train_loader, val_loader


def build_model(device: torch.device) -> nn.Module:
    logger.info("Building MobileNetV3-Large with pretrained ImageNet-1K V2 weights...")
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
    t0 = time.time()

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

        if (batch_idx + 1) % 50 == 0 or (batch_idx + 1) == len(loader):
            logger.info(
                f"Epoch {epoch:02d} [{batch_idx+1:03d}/{len(loader)}] "
                f"Loss: {total_loss/total:.4f}  Acc: {100.*correct/total:.2f}%"
            )

    elapsed = time.time() - t0
    return total_loss / total, 100.0 * correct / total, elapsed


@torch.no_grad()
def evaluate(model, loader, criterion, device):
    model.eval()
    total_loss = 0.0
    correct_top1 = 0
    correct_top3 = 0
    total = 0

    class_correct = [0] * NUM_CLASSES
    class_total = [0] * NUM_CLASSES

    for imgs, targets in loader:
        imgs, targets = imgs.to(device, non_blocking=True), targets.to(device, non_blocking=True)
        
        with autocast(device_type="cuda" if device.type == "cuda" else "cpu"):
            outputs = model(imgs)
            loss = criterion(outputs, targets)

        total_loss += loss.item() * imgs.size(0)
        total += imgs.size(0)

        _, pred1 = outputs.max(1)
        correct_top1 += pred1.eq(targets).sum().item()

        _, pred3 = outputs.topk(min(3, NUM_CLASSES), 1, True, True)
        correct_top3 += pred3.eq(targets.unsqueeze(1).expand_as(pred3)).any(1).sum().item()

        for t, p in zip(targets, pred1):
            class_total[t.item()] += 1
            if t == p:
                class_correct[t.item()] += 1

    per_class = {
        SUPPORTED_CATEGORIES[i]: {
            "correct": class_correct[i],
            "total": class_total[i],
            "accuracy_pct": round(100.0 * class_correct[i] / class_total[i], 2) if class_total[i] > 0 else 0.0
        }
        for i in range(NUM_CLASSES)
    }

    return total_loss / total, 100.0 * correct_top1 / total, 100.0 * correct_top3 / total, per_class


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=10, help="Total epochs (warmup + finetune)")
    parser.add_argument("--warmup-epochs", type=int, default=3, help="Warmup epochs with frozen backbone")
    parser.add_argument("--batch-size", type=int, default=64, help="Batch size")
    parser.add_argument("--lr-warmup", type=float, default=1e-3, help="Learning rate for warmup")
    parser.add_argument("--lr-finetune", type=float, default=2e-4, help="Learning rate for full finetuning")
    parser.add_argument("--workers", type=int, default=4, help="DataLoader workers")
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Using device: {device} ({torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'})")

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    train_loader, val_loader = get_dataloaders(batch_size=args.batch_size, num_workers=args.workers)

    model = build_model(device)
    criterion = nn.CrossEntropyLoss()
    scaler = GradScaler("cuda") if device.type == "cuda" else None

    best_val_top1 = 0.0
    history = []

    # -------------------------------------------------------------
    # Phase 1: Warmup (Head only)
    # -------------------------------------------------------------
    logger.info(f"\n{'='*60}\nPHASE 1: Warmup ({args.warmup_epochs} epochs) - Training classifier head only\n{'='*60}")
    set_backbone_trainable(model, False)
    optimizer = optim.AdamW(filter(lambda p: p.requires_grad, model.parameters()), lr=args.lr_warmup, weight_decay=1e-4)
    scheduler = CosineAnnealingLR(optimizer, T_max=args.warmup_epochs, eta_min=1e-5)

    for epoch in range(1, args.warmup_epochs + 1):
        tr_loss, tr_acc, elapsed = train_epoch(model, train_loader, criterion, optimizer, scaler, device, epoch)
        val_loss, val_top1, val_top3, per_class = evaluate(model, val_loader, criterion, device)
        scheduler.step()

        logger.info(
            f"Epoch {epoch:02d}/{args.warmup_epochs} [WARMUP] "
            f"Train Loss: {tr_loss:.4f} Acc: {tr_acc:.2f}% | "
            f"Val Loss: {val_loss:.4f} Top-1: {val_top1:.2f}% Top-3: {val_top3:.2f}% ({elapsed:.1f}s)"
        )

        history.append({
            "epoch": epoch, "phase": "warmup",
            "train_loss": round(tr_loss, 4), "train_acc": round(tr_acc, 2),
            "val_loss": round(val_loss, 4), "val_top1": round(val_top1, 2), "val_top3": round(val_top3, 2),
        })

        if val_top1 > best_val_top1:
            best_val_top1 = val_top1
            torch.save(model.state_dict(), str(CHECKPOINT_PATH))
            logger.info(f"  ★ New best model checkpoint saved: {val_top1:.2f}%")

    # -------------------------------------------------------------
    # Phase 2: Full Fine-tuning
    # -------------------------------------------------------------
    finetune_epochs = args.epochs - args.warmup_epochs
    if finetune_epochs > 0:
        logger.info(f"\n{'='*60}\nPHASE 2: Full Fine-Tuning ({finetune_epochs} epochs) - Unfreezing all layers\n{'='*60}")
        set_backbone_trainable(model, True)
        optimizer = optim.AdamW(model.parameters(), lr=args.lr_finetune, weight_decay=1e-4)
        scheduler = CosineAnnealingLR(optimizer, T_max=finetune_epochs, eta_min=1e-6)

        for offset in range(1, finetune_epochs + 1):
            epoch = args.warmup_epochs + offset
            tr_loss, tr_acc, elapsed = train_epoch(model, train_loader, criterion, optimizer, scaler, device, epoch)
            val_loss, val_top1, val_top3, per_class = evaluate(model, val_loader, criterion, device)
            scheduler.step()

            logger.info(
                f"Epoch {epoch:02d}/{args.epochs} [FINETUNE] "
                f"Train Loss: {tr_loss:.4f} Acc: {tr_acc:.2f}% | "
                f"Val Loss: {val_loss:.4f} Top-1: {val_top1:.2f}% Top-3: {val_top3:.2f}% ({elapsed:.1f}s)"
            )

            history.append({
                "epoch": epoch, "phase": "finetune",
                "train_loss": round(tr_loss, 4), "train_acc": round(tr_acc, 2),
                "val_loss": round(val_loss, 4), "val_top1": round(val_top1, 2), "val_top3": round(val_top3, 2),
            })

            if val_top1 > best_val_top1:
                best_val_top1 = val_top1
                torch.save(model.state_dict(), str(CHECKPOINT_PATH))
                logger.info(f"  ★ New best model checkpoint saved: {val_top1:.2f}%")

    # -------------------------------------------------------------
    # Final Evaluation with Best Weights
    # -------------------------------------------------------------
    logger.info(f"\n{'='*60}\nLoading best checkpoint from {CHECKPOINT_PATH} for final evaluation...\n{'='*60}")
    model.load_state_dict(torch.load(str(CHECKPOINT_PATH), map_location=device))
    _, final_top1, final_top3, final_per_class = evaluate(model, val_loader, criterion, device)

    logger.info(f"FINAL TOP-1 ACCURACY : {final_top1:.2f}%")
    logger.info(f"FINAL TOP-3 ACCURACY : {final_top3:.2f}%")
    logger.info("\nPer-Class Breakdown on Official 5,000 Food-101 Validation Split:")
    logger.info(f"{'Category':<24} {'Correct':>8} {'Total':>7} {'Acc %':>8}")
    logger.info("-" * 50)
    for cat, s in sorted(final_per_class.items(), key=lambda x: x[1]["accuracy_pct"], reverse=True):
        logger.info(f"{cat:<24} {s['correct']:>8} {s['total']:>7} {s['accuracy_pct']:>7.2f}%")

    summary = {
        "model_architecture": "MobileNetV3-Large",
        "checkpoint_path": str(CHECKPOINT_PATH),
        "dataset": "Food-101 (20 NutriGuide Categories)",
        "train_samples": len(train_loader.dataset),
        "val_samples": len(val_loader.dataset),
        "final_top1_accuracy": round(final_top1, 2),
        "final_top3_accuracy": round(final_top3, 2),
        "epochs_trained": args.epochs,
        "per_class_accuracy": final_per_class,
        "history": history,
    }

    with open(LOG_PATH, "w") as f:
        json.dump(summary, f, indent=2)

    logger.info(f"Training summary saved to: {LOG_PATH}")
    logger.info("TRAINING PIPELINE COMPLETE!")


if __name__ == "__main__":
    main()
