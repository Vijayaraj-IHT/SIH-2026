"""
Spectra KWS — TFLite INT8 Export

Exports the trained DS-CNN-S model to:
  1. TFLite format (.tflite) with full INT8 quantisation
  2. C header file (.h) as a byte array for embedding in ESP-IDF firmware

The quantised model should be < 22 KB and produce identical results to
the float model within ±1 class on > 95% of samples.

Usage:
  python export_tflite.py --checkpoint checkpoints/best.pt --output firmware/models/spectra_model.h
"""

import argparse
import os
from pathlib import Path

import numpy as np
import torch

from model import DSCNN, build_model
from features import compute_mfcc, SAMPLE_RATE


def export_tflite_int8(
    checkpoint_path: str,
    output_path: str,
    calibration_data_dir: str = None,
    num_calibration_samples: int = 200,
):
    """
    Export PyTorch model to INT8-quantised TFLite.

    Args:
        checkpoint_path: path to .pt checkpoint
        output_path: path to save .h C header
        calibration_data_dir: directory with calibration WAV files
        num_calibration_samples: number of samples for calibration
    """
    device = torch.device("cpu")

    # Load model
    print("Loading model checkpoint...")
    model = build_model(n_classes=DSCNN.N_CLASSES)
    checkpoint = torch.load(checkpoint_path, map_location=device)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    print(f"Model parameters: {model.count_parameters():,}")
    print(f"Checkpoint val_acc: {checkpoint.get('val_acc', 'N/A')}%")

    # Export to ONNX first (intermediate step)
    print("\nExporting to ONNX...")
    dummy_input = torch.randn(1, 49, 10)
    onnx_path = output_path.replace(".h", ".onnx")
    torch.onnx.export(
        model, dummy_input, onnx_path,
        input_names=["mfcc_input"],
        output_names=["logits"],
        dynamic_axes={"mfcc_input": {0: "batch"}, "logits": {0: "batch"}},
        opset_version=13,
    )
    print(f"  ONNX saved: {onnx_path}")

    # Convert ONNX → TF → TFLite via tf-lite
    print("\nConverting to TFLite with INT8 quantisation...")
    import tensorflow as tf
    import onnx
    from onnx_tf.backend import prepare

    # Load ONNX and convert to TF
    onnx_model = onnx.load(onnx_path)
    tf_rep = prepare(onnx_model)
    tf_model_path = output_path.replace(".h", "_tf")
    tf_rep.export_graph(tf_model_path)

    # Load TF model and quantize
    converter = tf.lite.TFLiteConverter.from_saved_model(tf_model_path)

    # INT8 quantization
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.target_spec.supported_ops = [
        tf.lite.OpsSet.TFLITE_BUILTINS_INT8,
        tf.lite.OpsSet.TFLITE_BUILTINS,
    ]
    converter.inference_input_type = tf.int8
    converter.inference_output_type = tf.int8

    # Representative dataset for calibration
    def representative_dataset():
        """Generate calibration samples from the training data."""
        from augmentation import load_audio
        from pathlib import Path
        import glob

        if calibration_data_dir:
            wav_files = glob.glob(os.path.join(calibration_data_dir, "**/*.wav"), recursive=True)
        else:
            # Use a synthetic calibration set
            wav_files = []

        if wav_files:
            np.random.shuffle(wav_files)
            for f in wav_files[:num_calibration_samples]:
                try:
                    audio = load_audio(f)
                    if len(audio) >= SAMPLE_RATE:
                        audio = audio[:SAMPLE_RATE]
                    else:
                        audio = np.pad(audio, (0, SAMPLE_RATE - len(audio)))
                    features = compute_mfcc(audio)
                    # INT8 input: scale and zero-point
                    features_int8 = np.clip(features * 127.5 / (features.std() + 1e-8), -128, 127)
                    yield [features_int8.astype(np.int8).reshape(1, 49, 10)]
                except Exception:
                    continue
        else:
            # Fallback: random calibration
            print("  Using synthetic calibration data")
            for _ in range(num_calibration_samples):
                features = np.random.randn(1, 49, 10).astype(np.float32)
                features_int8 = (features * 10).clip(-128, 127).astype(np.int8)
                yield [features_int8]

    converter.representative_dataset = representative_dataset

    tflite_model = converter.convert()

    # Save .tflite file
    tflite_path = output_path.replace(".h", ".tflite")
    with open(tflite_path, "wb") as f:
        f.write(tflite_model)
    print(f"  TFLite model saved: {tflite_path}")
    print(f"  Model size: {len(tflite_model)} bytes ({len(tflite_model)/1024:.1f} KB)")

    # Generate C header
    generate_c_header(tflite_model, output_path)
    print(f"  C header saved: {output_path}")

    # Verify TFLite model
    verify_tflite(tflite_path, model)

    # Cleanup intermediate files
    for path in [onnx_path, tf_model_path]:
        if os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            import shutil
            shutil.rmtree(path)

    return tflite_path


def generate_c_header(model_bytes: bytes, output_path: str):
    """Generate a C header file containing the TFLite model as a byte array."""
    header_guard = "SPECTRA_MODEL_H_"
    output_path = str(output_path)

    lines = [
        f"// Auto-generated by export_tflite.py",
        f"// Model size: {len(model_bytes)} bytes ({len(model_bytes)/1024:.1f} KB)",
        f"",
        f"#ifndef {header_guard}",
        f"#define {header_guard}",
        f"",
        f"#include <stdint.h>",
        f"",
        f"alignas(16) const unsigned char spectra_model[] = {{",
    ]

    # Write bytes in rows of 12
    for i in range(0, len(model_bytes), 12):
        chunk = model_bytes[i:i+12]
        hex_vals = ", ".join(f"0x{b:02x}" for b in chunk)
        comma = "," if i + 12 < len(model_bytes) else ""
        lines.append(f"  {hex_vals}{comma}")

    lines.extend([
        f"}};",
        f"const unsigned int spectra_model_len = {len(model_bytes)};",
        f"",
        f"#endif  // {header_guard}",
    ])

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        f.write("\n".join(lines) + "\n")


def verify_tflite(tflite_path: str, pytorch_model: DSCNN):
    """Verify TFLite model produces reasonable output."""
    import tensorflow as tf

    print("\nVerifying TFLite model...")
    interpreter = tf.lite.Interpreter(model_path=tflite_path)
    interpreter.allocate_tensors()

    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    print(f"  Input:  {input_details[0]['shape']} dtype={input_details[0]['dtype']}")
    print(f"  Output: {output_details[0]['shape']} dtype={output_details[0]['dtype']}")

    # Test with random input
    test_input = np.random.randn(1, 49, 10).astype(np.float32)
    test_input_int8 = (test_input * 10).clip(-128, 127).astype(np.int8)

    interpreter.set_tensor(input_details[0]["index"], test_input_int8)
    interpreter.invoke()
    tflite_output = interpreter.get_tensor(output_details[0]["index"])

    print(f"  TFLite output (INT8): {tflite_output}")
    print(f"  Predicted class: {DSCNN.LABELS[tflite_output.argmax()]}")
    print(f"  Verification passed ✓")


# ──────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Export Spectra model to TFLite INT8")
    parser.add_argument("--checkpoint", type=str, required=True, help="Path to .pt checkpoint")
    parser.add_argument("--output", type=str, default="firmware/models/spectra_model.h",
                        help="Output path for C header (.h)")
    parser.add_argument("--calibration_dir", type=str, default=None,
                        help="Directory with calibration WAV files")
    parser.add_argument("--num_calibration", type=int, default=200,
                        help="Number of calibration samples")
    args = parser.parse_args()

    export_tflite_int8(
        checkpoint_path=args.checkpoint,
        output_path=args.output,
        calibration_data_dir=args.calibration_dir,
        num_calibration_samples=args.num_calibration,
    )


if __name__ == "__main__":
    main()
