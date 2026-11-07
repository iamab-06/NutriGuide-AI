"""
NutriGuide AI - Food Image Classifier Training Script
======================================================
Fine-tunes MobileNetV3-Large on a 20-class Food-101 subset.

Usage:
    python train_classifier.py [--epochs 20] [--batch-size 64] [--lr 1e-3]

Training Strategy (Transfer Learning):
    Phase 1 (warm-up): Freeze backbone, train only the new 20-class head
                       for a few epochs to avoid destroying pretrained features.
    Phase 2 (fine-tune): Unfreeze backbone, train end-to-end with a low LR
                         to adapt features to food images.

Output:
    models/nutriguide_classifier.pth   — best model weights (state_dict)
    models/training_log.json           — epoch-by-epoch metrics
    models/class_to_idx.json           — class-to-index mapping for verification
"""

import argparse
import json
import os
import time
from pathlib import Path

import torch
import torch.nn as nn
import torch.optim as optim
from torch.optim.lr_scheduler import CosineAnnealingLR
from torch.utils.data import DataLoader, Subset
import torchvision.transforms as transforms
import torchvision.datasets as datasets
from torchvision import models

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "datasets" / "food101"
MODELS_DIR = BASE_DIR / "models"
CHECKPOINT_PATH = MODELS_DIR / "nutriguide_classifier.pth"
LOG_PATH = MODELS_DIR / "training_log.json"
CLASS_IDX_PATH = MODELS_DIR / "class_to_idx.json"

# Must match app/core/categories.py SUPPORTED_CATEGORIES order
SUPPORTED_CATEGORIES = [
    "apple_pie",
    "caesar_salad",
    "chicken_curry",
    "chocolate_cake",
    "donuts",
    "french_fries",
    "fried_rice",
    "hamburger",
    "hot_dog",
    "ice_cream",
    "omelette",
    "pancakes",
    "pizza",
    "ramen",
    "samosa",
    "spaghetti_bolognese",
    "spring_rolls",
    "steak",
    "sushi",
    "waffles",
]
NUM_CLASSES = len(SUPPORTED_CATEGORIES)  # 20


# ---------------------------------------------------------------------------
# Dataset helpers
# ---------------------------------------------------------------------------
def get_transforms(is_train: bool):
    """Data augmentation for training; deterministic preprocessing for validation."""
    if is_train:
        return transforms.Compose([
            transforms.RandomResizedCrop(224, scale=(0.7, 1.0)),
            transforms.RandomHorizontalFlip(),
            transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.3, hue=0.05),
            transforms.RandomRotation(15),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225]),
        ])
    else:
        return transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225]),
        ])


def prepare_dataset():
    """
    Download Food-101 via torchvision and build 20-class train/val splits.
    
    Food-101 provides official train (750/class) and test (250/class) splits.
    We use the official split to prevent leakage.
    """
    print(f"\n[Dataset] Downloading Food-101 to {DATA_DIR} ...")
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Download full Food-101 (will be cached)
    full_train = datasets.Food101(root=DATA_DIR, split="train", download=True,
                                  transform=get_transforms(is_train=True))
    full_test = datasets.Food101(root=DATA_DIR, split="test", download=True,
                                 transform=get_transforms(is_train=False))

    # Food-101 class names (101 total) → map our 20 to their indices
    # torchvision Food101 class_to_idx maps class_name -> label_index
    class_to_idx = full_train.class_to_idx  # dict: "class_name" -> int

    # Verify all 20 categories exist in Food-101
    missing = [c for c in SUPPORTED_CATEGORIES if c not in class_to_idx]
    if missing:
        raise ValueError(f"These categories are NOT in Food-101: {missing}")

    # Build label remap: Food-101 index → our 0-19 index
    food101_idx_to_ours = {}
    for our_idx, cat in enumerate(SUPPORTED_CATEGORIES):
        food101_idx = class_to_idx[cat]
        food101_idx_to_ours[food101_idx] = our_idx

    print(f"[Dataset] Found all {NUM_CLASSES} categories in Food-101.")

    # Filter datasets to only our 20 classes
    def filter_indices(dataset):
        targets = dataset.targets if hasattr(dataset, "targets") else [
            dataset._labels[i] for i in range(len(dataset))
        ]
        return [i for i, lbl in enumerate(targets) if lbl in food101_idx_to_ours]

    train_indices = filter_indices(full_train)
    test_indices = filter_indices(full_test)

    print(f"[Dataset] Train samples: {len(train_indices)}")
    print(f"[Dataset] Test  samples: {len(test_indices)}")

    # Wrap with remapped labels
    train_dataset = RemappedSubset(full_train, train_indices, food101_idx_to_ours)
    test_dataset = RemappedSubset(full_test, test_indices, food101_idx_to_ours)

    return train_dataset, test_dataset


class RemappedSubset(torch.utils.data.Dataset):
    """Dataset subset with remapped labels (Food-101 indices → our 0-19 indices)."""

    def __init__(self, dataset, indices, label_remap):
        self.dataset = dataset
        self.indices = indices
        self.label_remap = label_remap

    def __len__(self):
        return len(self.indices)

    def __getitem__(self, idx):
        img, original_label = self.dataset[self.indices[idx]]
        new_label = self.label_remap[original_label]
        return img, new_label


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------
def build_model(num_classes: int, device: torch.device) -> nn.Module:
    """Build MobileNetV3-Large with a fresh 20-class head."""
    model = models.mobilenet_v3_large(weights=models.MobileNet_V3_Large_Weights.IMAGENET1K_V2)
    in_features = model.classifier[3].in_features
    model.classifier[3] = nn.Linear(in_features, num_classes)
    return model.to(device)


def freeze_backbone(model: nn.Module):
    """Freeze all layers except the classifier head."""
    for name, param in model.named_parameters():
        if "classifier" not in name:
            param.requires_grad = False


def unfreeze_all(model: nn.Module):
    """Unfreeze all parameters for end-to-end fine-tuning."""
    for param in model.parameters():
        param.requires_grad = True


# ---------------------------------------------------------------------------
# Training loop
# ---------------------------------------------------------------------------
def train_one_epoch(model, loader, criterion, optimizer, device, epoch):
    model.train()
    total_loss = 0.0
    correct = 0
    total = 0
    start = time.time()

    for batch_idx, (imgs, labels) in enumerate(loader):
        imgs, labels = imgs.to(device), labels.to(device)
        optimizer.zero_grad()
        outputs = model(imgs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        total_loss += loss.item() * imgs.size(0)
        _, predicted = outputs.max(1)
        correct += predicted.eq(labels).sum().item()
        total += imgs.size(0)

        if (batch_idx + 1) % 20 == 0:
            print(f"  Epoch {epoch} [{batch_idx+1}/{len(loader)}] "
                  f"Loss: {total_loss/total:.4f}  Acc: {100.*correct/total:.1f}%")

    elapsed = time.time() - start
    return total_loss / total, 100.0 * correct / total, elapsed


@torch.no_grad()
def evaluate(model, loader, criterion, device):
    model.eval()
    total_loss = 0.0
    correct_top1 = 0
    correct_top3 = 0
    total = 0

    # Per-class tracking
    class_correct = [0] * NUM_CLASSES
    class_total = [0] * NUM_CLASSES

    for imgs, labels in loader:
        imgs, labels = imgs.to(device), labels.to(device)
        outputs = model(imgs)
        loss = criterion(outputs, labels)

        total_loss += loss.item() * imgs.size(0)
        total += imgs.size(0)

        # Top-1
        _, pred1 = outputs.max(1)
        correct_top1 += pred1.eq(labels).sum().item()

        # Top-3
        _, pred3 = outputs.topk(min(3, NUM_CLASSES), 1, True, True)
        correct_top3 += pred3.eq(labels.unsqueeze(1).expand_as(pred3)).any(1).sum().item()

        # Per-class
        for label, pred in zip(labels, pred1):
            class_total[label.item()] += 1
            if label == pred:
                class_correct[label.item()] += 1

    per_class = {
        SUPPORTED_CATEGORIES[i]: {
            "correct": class_correct[i],
            "total": class_total[i],
            "accuracy": 100.0 * class_correct[i] / class_total[i] if class_total[i] > 0 else 0.0
        }
        for i in range(NUM_CLASSES)
    }

    return (
        total_loss / total,
        100.0 * correct_top1 / total,
        100.0 * correct_top3 / total,
        per_class,
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="NutriGuide AI Classifier Training")
    parser.add_argument("--epochs", type=int, default=20, help="Total training epochs")
    parser.add_argument("--warmup-epochs", type=int, default=5, help="Epochs with frozen backbone")
    parser.add_argument("--batch-size", type=int, default=64, help="Batch size")
    parser.add_argument("--lr", type=float, default=1e-3, help="Head-only learning rate (warmup)")
    parser.add_argument("--lr-finetune", type=float, default=1e-4, help="Full LR for fine-tune phase")
    parser.add_argument("--workers", type=int, default=4, help="DataLoader workers")
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"\n[Setup] Device: {device}")
    if torch.cuda.is_available():
        print(f"[Setup] GPU: {torch.cuda.get_device_name(0)}")
    print(f"[Setup] Epochs: {args.epochs} (warmup: {args.warmup_epochs})")
    print(f"[Setup] Batch: {args.batch_size}  LR head: {args.lr}  LR fine: {args.lr_finetune}")

    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    # Dataset
    train_dataset, test_dataset = prepare_dataset()

    train_loader = DataLoader(
        train_dataset, batch_size=args.batch_size, shuffle=True,
        num_workers=args.workers, pin_memory=True if torch.cuda.is_available() else False,
        persistent_workers=True if args.workers > 0 else False
    )
    test_loader = DataLoader(
        test_dataset, batch_size=args.batch_size, shuffle=False,
        num_workers=args.workers, pin_memory=True if torch.cuda.is_available() else False,
        persistent_workers=True if args.workers > 0 else False
    )

    # Model
    model = build_model(NUM_CLASSES, device)

    # Save class-to-index mapping for verification
    class_to_idx = {cat: idx for idx, cat in enumerate(SUPPORTED_CATEGORIES)}
    with open(CLASS_IDX_PATH, "w") as f:
        json.dump(class_to_idx, f, indent=2)
    print(f"[Setup] Class→index mapping saved to {CLASS_IDX_PATH}")

    criterion = nn.CrossEntropyLoss()
    training_log = []
    best_val_acc = 0.0

    # -----------------------------------------------------------------------
    # Phase 1: Warm-up — train head only
    # -----------------------------------------------------------------------
    print(f"\n{'='*60}")
    print(f"PHASE 1: Warm-up (epochs 1-{args.warmup_epochs}) — head only")
    print(f"{'='*60}")
    freeze_backbone(model)
    optimizer = optim.Adam(
        filter(lambda p: p.requires_grad, model.parameters()),
        lr=args.lr, weight_decay=1e-4
    )
    scheduler = CosineAnnealingLR(optimizer, T_max=args.warmup_epochs, eta_min=1e-5)

    for epoch in range(1, args.warmup_epochs + 1):
        train_loss, train_acc, elapsed = train_one_epoch(
            model, train_loader, criterion, optimizer, device, epoch
        )
        val_loss, val_acc_top1, val_acc_top3, per_class = evaluate(
            model, test_loader, criterion, device
        )
        scheduler.step()

        print(f"\nEpoch {epoch:02d}/{args.warmup_epochs} [WARMUP] "
              f"| Train Loss: {train_loss:.4f} Acc: {train_acc:.1f}% "
              f"| Val Loss: {val_loss:.4f} Top-1: {val_acc_top1:.1f}% Top-3: {val_acc_top3:.1f}% "
              f"| Time: {elapsed:.1f}s")

        entry = {
            "epoch": epoch, "phase": "warmup",
            "train_loss": round(train_loss, 4), "train_acc": round(train_acc, 2),
            "val_loss": round(val_loss, 4), "val_top1": round(val_acc_top1, 2),
            "val_top3": round(val_acc_top3, 2),
        }
        training_log.append(entry)

        if val_acc_top1 > best_val_acc:
            best_val_acc = val_acc_top1
            torch.save(model.state_dict(), CHECKPOINT_PATH)
            print(f"  ✓ Saved best model — Val Top-1: {val_acc_top1:.1f}%")

    # -----------------------------------------------------------------------
    # Phase 2: Fine-tune — unfreeze all
    # -----------------------------------------------------------------------
    fine_epochs = args.epochs - args.warmup_epochs
    if fine_epochs > 0:
        print(f"\n{'='*60}")
        print(f"PHASE 2: Fine-tune (epochs {args.warmup_epochs+1}-{args.epochs}) — end-to-end")
        print(f"{'='*60}")
        unfreeze_all(model)
        optimizer = optim.Adam(model.parameters(), lr=args.lr_finetune, weight_decay=1e-4)
        scheduler = CosineAnnealingLR(optimizer, T_max=fine_epochs, eta_min=1e-6)

        for epoch_offset in range(1, fine_epochs + 1):
            epoch = args.warmup_epochs + epoch_offset
            train_loss, train_acc, elapsed = train_one_epoch(
                model, train_loader, criterion, optimizer, device, epoch
            )
            val_loss, val_acc_top1, val_acc_top3, per_class = evaluate(
                model, test_loader, criterion, device
            )
            scheduler.step()

            print(f"\nEpoch {epoch:02d}/{args.epochs} [FINETUNE] "
                  f"| Train Loss: {train_loss:.4f} Acc: {train_acc:.1f}% "
                  f"| Val Loss: {val_loss:.4f} Top-1: {val_acc_top1:.1f}% Top-3: {val_acc_top3:.1f}% "
                  f"| Time: {elapsed:.1f}s")

            entry = {
                "epoch": epoch, "phase": "finetune",
                "train_loss": round(train_loss, 4), "train_acc": round(train_acc, 2),
                "val_loss": round(val_loss, 4), "val_top1": round(val_acc_top1, 2),
                "val_top3": round(val_acc_top3, 2),
            }
            training_log.append(entry)

            if val_acc_top1 > best_val_acc:
                best_val_acc = val_acc_top1
                torch.save(model.state_dict(), CHECKPOINT_PATH)
                print(f"  ✓ Saved best model — Val Top-1: {val_acc_top1:.1f}%")

    # -----------------------------------------------------------------------
    # Final evaluation with best checkpoint
    # -----------------------------------------------------------------------
    print(f"\n{'='*60}")
    print("FINAL EVALUATION with best checkpoint")
    print(f"{'='*60}")
    state = torch.load(CHECKPOINT_PATH, map_location=device)
    model.load_state_dict(state)
    _, final_top1, final_top3, final_per_class = evaluate(model, test_loader, criterion, device)

    print(f"\nFinal Top-1 Accuracy : {final_top1:.2f}%")
    print(f"Final Top-3 Accuracy : {final_top3:.2f}%")
    print("\nPer-class accuracy (on official Food-101 test split):")
    print(f"{'Category':<25} {'Correct':>8} {'Total':>7} {'Acc%':>7}")
    print("-" * 52)
    for cat, stats in sorted(final_per_class.items(), key=lambda x: x[1]["accuracy"]):
        print(f"{cat:<25} {stats['correct']:>8} {stats['total']:>7} {stats['accuracy']:>6.1f}%")

    # Save log
    final_summary = {
        "best_val_top1": round(best_val_acc, 2),
        "final_top1": round(final_top1, 2),
        "final_top3": round(final_top3, 2),
        "epochs": args.epochs,
        "warmup_epochs": args.warmup_epochs,
        "num_classes": NUM_CLASSES,
        "categories": SUPPORTED_CATEGORIES,
        "per_class": final_per_class,
        "checkpoint": str(CHECKPOINT_PATH),
    }
    with open(LOG_PATH, "w") as f:
        json.dump({"summary": final_summary, "epochs": training_log}, f, indent=2)

    print(f"\n[Done] Best checkpoint: {CHECKPOINT_PATH}")
    print(f"[Done] Training log:    {LOG_PATH}")
    print(f"[Done] Best Val Top-1:  {best_val_acc:.2f}%")


if __name__ == "__main__":
    main()
