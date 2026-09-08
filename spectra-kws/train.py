"""
Spectra KWS — Training Pipeline

Trains DS-CNN-S on a 3-class keyword spotting task:
  - spectra  : the wake word (positive class)
  - unknown  : 35 words from Google Speech Commands
  - silence  : background noise / empty recordings

Dataset layout (dataset/):
  positives/   → "Spectra" recordings (4 conditions: slow/fast × near/far)
  negatives/   → Google Speech Commands words
  confusion/   → "spectrum", "expect", "extra", etc.
  background/  → ambient noise WAV files

Usage:
  python train.py --data_dir dataset --epochs 100 --batch_size 64
"""

import argparse
import json
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader, WeightedRandomSampler
from torch.utils.tensorboard import SummaryWriter

from model import DSCNN, build_model
from features import compute_mfcc, SAMPLE_RATE
from augmentation import augment_sample, load_audio


# ──────────────────────────────────────────────────────────────────────
# Dataset
# ──────────────────────────────────────────────────────────────────────

class KWSDataset(Dataset):
    """
    Keyword Spotting Dataset.

    Expects directory structure:
        data_dir/
            positives/    *.wav    → label 0 (spectra)
            negatives/    *.wav    → label 1 (unknown)
            confusion/    *.wav    → label 1 (unknown)
            background/   *.wav    → label 2 (silence)
    """

    LABEL_MAP = {
        "positives": 0,   # spectra
        "negatives": 1,   # unknown
        "confusion": 1,   # unknown (confusion words are also unknown)
        "background": 2,  # silence
    }

    def __init__(
        self,
        data_dir: str,
        augment: bool = False,
        augment_factor: int = 3,
        target_sr: int = SAMPLE_RATE,
    ):
        self.data_dir = Path(data_dir)
        self.augment = augment
        self.augment_factor = augment_factor
        self.target_sr = target_sr

        # Gather noise files for augmentation
        noise_dir = self.data_dir / "background"
        self.noise_files = [str(f) for f in noise_dir.glob("*.wav")] if noise_dir.exists() else []

        # Scan all audio files
        self.samples: List[Tuple[str, int]] = []
        for subdir, label in self.LABEL_MAP.items():
            subdir_path = self.data_dir / subdir
            if not subdir_path.exists():
                print(f"  [WARN] {subdir_path} not found, skipping")
                continue
            wav_files = sorted(subdir_path.glob("*.wav"))
            print(f"  {subdir}: {len(wav_files)} files → label {label}")
            for f in wav_files:
                self.samples.append((str(f), label))

        # Count classes
        self.class_counts = {0: 0, 1: 0, 2: 0}
        for _, label in self.samples:
            self.class_counts[label] += 1

        print(f"\n  Total samples: {len(self.samples)}")
        print(f"  Class distribution: spectra={self.class_counts[0]}, "
              f"unknown={self.class_counts[1]}, silence={self.class_counts[2]}")

    def __len__(self) -> int:
        if self.augment:
            return len(self.samples) * self.augment_factor
        return len(self.samples)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        # Map augmented index back to original
        original_idx = idx % len(self.samples)
        filepath, label = self.samples[original_idx]

        # Load audio
        audio = load_audio(filepath, target_sr=self.target_sr)

        # Ensure exactly 1 second
        target_len = self.target_sr
        if len(audio) > target_len:
            audio = audio[:target_len]
        elif len(audio) < target_len:
            audio = np.pad(audio, (0, target_len - len(audio)))

        # Apply augmentation (for augmented indices)
        if self.augment and idx >= len(self.samples):
            audio = augment_sample(audio, noise_files=self.noise_files, sr=self.target_sr)

        # Extract features
        features = compute_mfcc(audio)  # (49, 10)
        features = torch.from_numpy(features)  # float32

        return features, label


def build_weighted_sampler(dataset: KWSDataset) -> WeightedRandomSampler:
    """Create a weighted sampler to handle class imbalance."""
    labels = [label for _, label in dataset.samples]
    class_counts = np.array([dataset.class_counts[i] for i in range(3)], dtype=np.float32)
    weights_per_class = 1.0 / (class_counts + 1)
    sample_weights = [weights_per_class[label] for label in labels]
    # Repeat weights for augmented samples
    if dataset.augment:
        sample_weights = sample_weights * dataset.augment_factor
    return WeightedRandomSampler(sample_weights, len(sample_weights), replacement=True)


# ──────────────────────────────────────────────────────────────────────
# Training loop
# ──────────────────────────────────────────────────────────────────────

def train_one_epoch(
    model: DSCNN,
    loader: DataLoader,
    criterion: nn.Module,
    optimizer: optim.Optimizer,
    device: torch.device,
    epoch: int,
    writer: SummaryWriter,
) -> Tuple[float, float]:
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0

    for batch_idx, (features, labels) in enumerate(loader):
        features = features.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()
        outputs = model(features)
        loss = criterion(outputs, labels)
        loss.backward()

        # Gradient clipping
        nn.utils.clip_grad_norm_(model.parameters(), max_norm=5.0)
        optimizer.step()

        running_loss += loss.item() * features.size(0)
        _, predicted = outputs.max(1)
        total += labels.size(0)
        correct += predicted.eq(labels).sum().item()

    avg_loss = running_loss / total
    accuracy = 100.0 * correct / total

    global_step = epoch * len(loader)
    writer.add_scalar("train/loss", avg_loss, global_step)
    writer.add_scalar("train/accuracy", accuracy, global_step)

    return avg_loss, accuracy


@torch.no_grad()
def evaluate(
    model: DSCNN,
    loader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
) -> Tuple[float, float, Dict]:
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0
    class_correct = {0: 0, 1: 0, 2: 0}
    class_total = {0: 0, 1: 0, 2: 0}

    for features, labels in loader:
        features = features.to(device)
        labels = labels.to(device)

        outputs = model(features)
        loss = criterion(outputs, labels)

        running_loss += loss.item() * features.size(0)
        _, predicted = outputs.max(1)
        total += labels.size(0)
        correct += predicted.eq(labels).sum().item()

        for c in range(3):
            mask = labels == c
            class_total[c] += mask.sum().item()
            class_correct[c] += (predicted[mask] == c).sum().item()

    avg_loss = running_loss / total
    accuracy = 100.0 * correct / total

    per_class = {}
    label_names = DSCNN.LABELS
    for c in range(3):
        if class_total[c] > 0:
            per_class[label_names[c]] = {
                "accuracy": 100.0 * class_correct[c] / class_total[c],
                "count": class_total[c],
            }

    return avg_loss, accuracy, per_class


# ──────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Train Spectra DS-CNN-S model")
    parser.add_argument("--data_dir", type=str, required=True, help="Path to dataset/")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--batch_size", type=int, default=64)
    parser.add_argument("--lr", type=float, default=0.001)
    parser.add_argument("--weight_decay", type=float, default=1e-4)
    parser.add_argument("--augment_factor", type=int, default=3)
    parser.add_argument("--output_dir", type=str, default="checkpoints")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--patience", type=int, default=15, help="Early stopping patience")
    args = parser.parse_args()

    # Reproducibility
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    # Build datasets
    print("\n=== Loading datasets ===")
    print("Training set (with augmentation):")
    train_dataset = KWSDataset(args.data_dir, augment=True, augment_factor=args.augment_factor)
    print("\nValidation set (no augmentation):")
    val_dataset = KWSDataset(args.data_dir, augment=False)

    # Split: 80% train, 20% val
    n_total = len(train_dataset.samples)
    n_train = int(0.8 * n_total)
    n_val = n_total - n_train

    indices = torch.randperm(n_total).tolist()
    train_indices = indices[:n_train]
    val_indices = indices[n_train:]

    train_sampler = torch.utils.data.SubsetRandomSampler(
        [i * args.augment_factor + j for i in train_indices for j in range(args.augment_factor)]
    )
    val_sampler = torch.utils.data.SubsetRandomSampler(val_indices)

    train_loader = DataLoader(
        train_dataset, batch_size=args.batch_size, sampler=train_sampler,
        num_workers=4, pin_memory=True,
    )
    val_loader = DataLoader(
        val_dataset, batch_size=args.batch_size, sampler=val_sampler,
        num_workers=4, pin_memory=True,
    )

    # Build model
    model = build_model(n_classes=DSCNN.N_CLASSES).to(device)
    print(f"\nModel parameters: {model.count_parameters():,}")

    # Loss with class weights (handle imbalance)
    class_weights = torch.tensor([5.0, 1.0, 1.0], device=device)  # upweight spectra
    criterion = nn.CrossEntropyLoss(weight=class_weights)

    optimizer = optim.Adam(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='min', factor=0.5, patience=5, verbose=True,
    )

    # Output directory
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    writer = SummaryWriter(log_dir=str(out_dir / "logs"))

    # Save training config
    with open(out_dir / "config.json", "w") as f:
        json.dump(vars(args), f, indent=2)

    # Training loop
    best_val_loss = float("inf")
    patience_counter = 0

    print(f"\n{'=' * 60}")
    print(f"Training for {args.epochs} epochs")
    print(f"{'=' * 60}")

    for epoch in range(args.epochs):
        t0 = time.time()

        train_loss, train_acc = train_one_epoch(
            model, train_loader, criterion, optimizer, device, epoch, writer,
        )
        val_loss, val_acc, per_class = evaluate(
            model, val_loader, criterion, device,
        )

        scheduler.step(val_loss)

        elapsed = time.time() - t0
        lr = optimizer.param_groups[0]["lr"]

        print(f"Epoch {epoch+1:3d}/{args.epochs} | "
              f"Train Loss: {train_loss:.4f} Acc: {train_acc:.1f}% | "
              f"Val Loss: {val_loss:.4f} Acc: {val_acc:.1f}% | "
              f"LR: {lr:.6f} | {elapsed:.1f}s")

        # Per-class accuracy
        for cls_name, cls_info in per_class.items():
            print(f"  {cls_name}: {cls_info['accuracy']:.1f}% ({cls_info['count']} samples)")

        # Log to tensorboard
        writer.add_scalar("val/loss", val_loss, epoch)
        writer.add_scalar("val/accuracy", val_acc, epoch)
        writer.add_scalar("lr", lr, epoch)
        for cls_name, cls_info in per_class.items():
            writer.add_scalar(f"val/acc_{cls_name}", cls_info["accuracy"], epoch)

        # Save best model
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "val_loss": val_loss,
                "val_acc": val_acc,
            }, out_dir / "best.pt")
            print(f"  → New best model saved (val_loss={val_loss:.4f})")
        else:
            patience_counter += 1

        # Early stopping
        if patience_counter >= args.patience:
            print(f"\nEarly stopping at epoch {epoch+1} (patience={args.patience})")
            break

    writer.close()

    print(f"\n{'=' * 60}")
    print(f"Training complete!")
    print(f"Best validation loss: {best_val_loss:.4f}")
    print(f"Best model saved to: {out_dir / 'best.pt'}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
