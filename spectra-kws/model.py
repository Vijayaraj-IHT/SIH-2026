"""
Spectra KWS — DS-CNN-S Model Definition

Depthwise-Separable Convolutional Neural Network for keyword spotting.
This is the "Hello Edge" architecture with ~22 k parameters.

Architecture:
  Input: (batch, 49, 10) — 49 time frames × 10 MFCC features

  1. Reshape to (batch, 49, 10, 1) — single channel "image"
  2. Conv2D:  64 filters, 3×3, stride 1, BN, ReLU
  3. DS-Block: depthwise 3×3 + pointwise 1×1, 64→64, BN, ReLU
  4. DS-Block: depthwise 3×3 + pointwise 1×1, 64→64, stride 2, BN, ReLU
  5. DS-Block: depthwise 3×3 + pointwise 1×1, 64→96, BN, ReLU
  6. DS-Block: depthwise 3×3 + pointwise 1×1, 96→96, stride 2, BN, ReLU
  7. DS-Block: depthwise 3×3 + pointwise 1×1, 96→128, BN, ReLU
  8. Global Average Pooling → (batch, 128)
  9. FC: 128 → 3 (spectra / unknown / silence)

All ops are INT8-quantisation friendly (conv, depthwise conv, ReLU, pool, FC).
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List


class DepthwiseSeparableConv(nn.Module):
    """Depthwise-separable convolution block: depthwise + pointwise + BN + ReLU."""

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        stride: int = 1,
        kernel_size: int = 3,
    ):
        super().__init__()
        padding = kernel_size // 2
        self.depthwise = nn.Conv2d(
            in_channels, in_channels,
            kernel_size=kernel_size, stride=stride,
            padding=padding, groups=in_channels, bias=False,
        )
        self.pointwise = nn.Conv2d(
            in_channels, out_channels,
            kernel_size=1, stride=1, bias=False,
        )
        self.bn = nn.BatchNorm2d(out_channels)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.depthwise(x)
        x = self.pointwise(x)
        x = self.bn(x)
        return F.relu(x, inplace=True)


class DSCNN(nn.Module):
    """
    DS-CNN-S: Small variant for keyword spotting.
    ~22 k parameters, < 40 KB inference RAM (INT8).
    """

    # Class labels — must match dataset organisation
    LABELS = ["spectra", "unknown", "silence"]
    N_CLASSES = len(LABELS)

    def __init__(self, n_classes: int = 3, in_features: int = 10):
        super().__init__()

        # Initial convolution
        self.conv = nn.Conv2d(1, 64, kernel_size=3, stride=1, padding=1, bias=False)
        self.bn0 = nn.BatchNorm2d(64)

        # Depthwise-separable blocks
        self.ds_blocks = nn.Sequential(
            # DS-Block 1: 64 → 64, stride 1
            DepthwiseSeparableConv(64, 64, stride=1),
            # DS-Block 2: 64 → 64, stride 2 (downsample time and freq)
            DepthwiseSeparableConv(64, 64, stride=2),
            # DS-Block 3: 64 → 96, stride 1
            DepthwiseSeparableConv(64, 96, stride=1),
            # DS-Block 4: 96 → 96, stride 2
            DepthwiseSeparableConv(96, 96, stride=2),
            # DS-Block 5: 96 → 128, stride 1
            DepthwiseSeparableConv(96, 128, stride=1),
        )

        # Global average pooling + FC
        self.fc = nn.Linear(128, n_classes, bias=True)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: (batch, 49, 10) — MFCC features

        Returns:
            logits: (batch, n_classes)
        """
        # Reshape to (batch, 1, 49, 10) — single channel
        if x.dim() == 3:
            x = x.unsqueeze(1)

        # Initial conv
        x = F.relu(self.bn0(self.conv(x)), inplace=True)

        # DS blocks
        x = self.ds_blocks(x)

        # Global average pooling
        x = F.adaptive_avg_pool2d(x, 1)  # (batch, 128, 1, 1)
        x = x.view(x.size(0), -1)        # (batch, 128)

        # Classification
        x = self.fc(x)                    # (batch, n_classes)
        return x

    def count_parameters(self) -> int:
        return sum(p.numel() for p in self.parameters() if p.requires_grad)


def build_model(n_classes: int = 3) -> DSCNN:
    """Build and return a fresh DS-CNN-S model."""
    model = DSCNN(n_classes=n_classes)
    return model


# ──────────────────────────────────────────────────────────────────────
# CLI — print model summary
# ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    model = build_model()
    print(f"DS-CNN-S Model Summary")
    print(f"{'=' * 50}")
    print(f"Classes: {model.LABELS}")
    print(f"Parameters: {model.count_parameters():,}")
    print(f"Model size (FP32): {model.count_parameters() * 4 / 1024:.1f} KB")
    print(f"Model size (INT8): {model.count_parameters() * 1 / 1024:.1f} KB")
    print()

    # Test forward pass
    dummy = torch.randn(1, 49, 10)
    out = model(dummy)
    print(f"Input shape:  {dummy.shape}")
    print(f"Output shape: {out.shape}")
    print(f"Output (logits): {out.detach().numpy()}")
    print(f"Output (probs):  {F.softmax(out, dim=1).detach().numpy()}")
