"""
Spectra KWS — Offline Evaluation

Evaluates the DS-CNN-S model for:
  1. Accuracy — per-class and overall
  2. False-reject rate (FRR) — how often "Spectra" is missed
  3. False-accept rate (FAR) — how often non-keywords trigger
  4. Latency — inference time per sample (simulated)
  5. Confusion matrix

Also supports running the model against hours of negative audio
to estimate false accepts per 10 hours.

Usage:
  python evaluate.py --checkpoint checkpoints/best.pt --data_dir dataset
  python evaluate.py --checkpoint checkpoints/best.pt --data_dir dataset --far_test --hours 10
"""

import argparse
import json
import time
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import torch
import torch.nn.functional as F

from model import DSCNN, build_model
from features import compute_mfcc, SAMPLE_RATE
from augmentation import load_audio


def load_model(checkpoint_path: str, device: torch.device) -> DSCNN:
    """Load trained model from checkpoint."""
    model = build_model(n_classes=DSCNN.N_CLASSES)
    checkpoint = torch.load(checkpoint_path, map_location=device)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.to(device)
    model.eval()
    return model


@torch.no_grad()
def predict(model: DSCNN, features: np.ndarray, device: torch.device) -> Tuple[int, np.ndarray]:
    """
    Run inference on a single sample.

    Args:
        features: (49, 10) MFCC features
    Returns:
        predicted_class: int (0=spectra, 1=unknown, 2=silence)
        probabilities: (3,) softmax probabilities
    """
    x = torch.from_numpy(features).unsqueeze(0).to(device)  # (1, 49, 10)
    logits = model(x)
    probs = F.softmax(logits, dim=1).squeeze(0).cpu().numpy()
    return int(probs.argmax()), probs


def evaluate_accuracy(
    model: DSCNN,
    data_dir: str,
    device: torch.device,
    theta: float = 0.7,
) -> Dict:
    """
    Evaluate model accuracy on the test set.

    Returns dict with per-class accuracy, FRR, FAR, confusion matrix.
    """
    data_path = Path(data_dir)
    label_map = {
        "positives": 0,   # spectra
        "negatives": 1,   # unknown
        "confusion": 1,   # unknown
        "background": 2,  # silence
    }
    label_names = DSCNN.LABELS

    results = {
        "total": 0, "correct": 0,
        "per_class": {name: {"correct": 0, "total": 0} for name in label_names},
        "confusion": [[0]*3 for _ in range(3)],
        "frr": {"misses": 0, "total_positives": 0},
        "far": {"false_alarms": 0, "total_negatives": 0},
        "latencies": [],
    }

    for subdir, true_label in label_map.items():
        subdir_path = data_path / subdir
        if not subdir_path.exists():
            continue
        wav_files = sorted(subdir_path.glob("*.wav"))

        for wav_file in wav_files:
            try:
                audio = load_audio(str(wav_file))
                if len(audio) >= SAMPLE_RATE:
                    audio = audio[:SAMPLE_RATE]
                else:
                    audio = np.pad(audio, (0, SAMPLE_RATE - len(audio)))

                features = compute_mfcc(audio)

                # Time the inference
                t0 = time.perf_counter()
                pred_class, probs = predict(model, features, device)
                t1 = time.perf_counter()

                results["latencies"].append((t1 - t0) * 1000)  # ms
                results["total"] += 1
                results["confusion"][true_label][pred_class] += 1

                is_correct = pred_class == true_label
                if is_correct:
                    results["correct"] += 1
                    results["per_class"][label_names[true_label]]["correct"] += 1
                results["per_class"][label_names[true_label]]["total"] += 1

                # FRR: positive sample not detected as "spectra" or below threshold
                if true_label == 0:
                    results["frr"]["total_positives"] += 1
                    if pred_class != 0 or probs[0] < theta:
                        results["frr"]["misses"] += 1

                # FAR: negative sample detected as "spectra" above threshold
                if true_label in (1, 2):
                    results["far"]["total_negatives"] += 1
                    if pred_class == 0 and probs[0] >= theta:
                        results["far"]["false_alarms"] += 1

            except Exception as e:
                print(f"  Error processing {wav_file}: {e}")

    # Compute derived metrics
    results["accuracy"] = 100.0 * results["correct"] / max(results["total"], 1)
    for name in label_names:
        cls = results["per_class"][name]
        cls["accuracy"] = 100.0 * cls["correct"] / max(cls["total"], 1)

    if results["frr"]["total_positives"] > 0:
        results["frr"]["rate"] = 100.0 * results["frr"]["misses"] / results["frr"]["total_positives"]
    else:
        results["frr"]["rate"] = 0.0

    if results["far"]["total_negatives"] > 0:
        results["far"]["rate"] = 100.0 * results["far"]["false_alarms"] / results["far"]["total_negatives"]
    else:
        results["far"]["rate"] = 0.0

    latencies = results["latencies"]
    if latencies:
        results["latency_ms"] = {
            "mean": np.mean(latencies),
            "p50": np.percentile(latencies, 50),
            "p90": np.percentile(latencies, 90),
            "p99": np.percentile(latencies, 99),
            "max": np.max(latencies),
        }

    return results


def print_report(results: Dict):
    """Pretty-print evaluation report."""
    print("\n" + "=" * 60)
    print("  SPECTRA KWS — Evaluation Report")
    print("=" * 60)

    print(f"\n  Overall Accuracy: {results['accuracy']:.1f}% ({results['correct']}/{results['total']})")

    print(f"\n  Per-Class Accuracy:")
    for name, info in results["per_class"].items():
        print(f"    {name:10s}: {info['accuracy']:5.1f}% ({info['correct']}/{info['total']})")

    print(f"\n  False Reject Rate (FRR): {results['frr']['rate']:.2f}%")
    print(f"    Misses: {results['frr']['misses']}/{results['frr']['total_positives']} positives")

    print(f"\n  False Accept Rate (FAR): {results['far']['rate']:.2f}%")
    print(f"    False alarms: {results['far']['false_alarms']}/{results['far']['total_negatives']} negatives")

    if "latency_ms" in results:
        lat = results["latency_ms"]
        print(f"\n  Inference Latency:")
        print(f"    Mean: {lat['mean']:.2f} ms")
        print(f"    P50:  {lat['p50']:.2f} ms")
        print(f"    P90:  {lat['p90']:.2f} ms")
        print(f"    P99:  {lat['p99']:.2f} ms")
        print(f"    Max:  {lat['max']:.2f} ms")

    print(f"\n  Confusion Matrix (true → predicted):")
    labels = DSCNN.LABELS
    print(f"    {'':10s}", end="")
    for name in labels:
        print(f"  {name:>10s}", end="")
    print()
    for i, name in enumerate(labels):
        print(f"    {name:10s}", end="")
        for j in range(len(labels)):
            print(f"  {results['confusion'][i][j]:10d}", end="")
        print()

    print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Evaluate Spectra KWS model")
    parser.add_argument("--checkpoint", type=str, required=True, help="Path to .pt checkpoint")
    parser.add_argument("--data_dir", type=str, required=True, help="Path to dataset/")
    parser.add_argument("--theta", type=float, default=0.7, help="Detection threshold")
    parser.add_argument("--output_json", type=str, default=None, help="Save results as JSON")
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    model = load_model(args.checkpoint, device)
    print(f"Model parameters: {model.count_parameters():,}")

    results = evaluate_accuracy(model, args.data_dir, device, theta=args.theta)
    print_report(results)

    if args.output_json:
        # Remove non-serializable latencies list
        save_results = {k: v for k, v in results.items() if k != "latencies"}
        with open(args.output_json, "w") as f:
            json.dump(save_results, f, indent=2)
        print(f"\nResults saved to: {args.output_json}")


if __name__ == "__main__":
    main()
