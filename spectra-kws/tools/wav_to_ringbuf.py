"""
Spectra — WAV to Ring Buffer Converter

Converts .wav audio files into the exact binary format that the ESP32-C5's
I2S DMA ring buffer stores. This is used for:

  1. Testing the MFCC C implementation against the Python reference
     (feed the same binary into both, compare outputs)
  2. Simulating the full firmware pipeline on a PC
  3. Generating test vectors for unit testing on the ESP32

The ring buffer format is:
  - Raw PCM samples (no header)
  - int16_t (signed 16-bit)
  - Little-endian (native on ESP32-C5 RISC-V)
  - Mono, 16 kHz
  - Sequential samples, no interleaving

This matches what the INMP441 microphone produces via I2S.

Usage:
  # Convert a WAV file to ring buffer binary
  python tools/wav_to_ringbuf.py input.wav output.bin

  # Convert + dump sample info
  python tools/wav_to_ringbuf.py input.wav output.bin --verbose

  # Generate a 1-second test tone
  python tools/wav_to_ringbuf.py --generate-tone 440 tone_440hz.bin

  # Generate silence
  python tools/wav_to_ringbuf.py --generate-silence silence.bin

  # Convert + generate C array header
  python tools/wav_to_ringbuf.py input.wav test_audio.h --as-c-header

  # Convert all WAVs in a directory
  python tools/wav_to_ringbuf.py dataset/positives/ output_bins/ --batch

This is Member 1's primary tool.
"""

import argparse
import struct
import sys
import os
from pathlib import Path
from typing import Optional, Tuple

import numpy as np


# ──────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────
TARGET_SAMPLE_RATE = 16000
TARGET_BIT_DEPTH = 16
TARGET_CHANNELS = 1          # mono
BYTES_PER_SAMPLE = 2         # int16_t
TARGET_DURATION_MS = 1000    # 1 second
TARGET_SAMPLES = TARGET_SAMPLE_RATE * TARGET_DURATION_MS // 1000  # 16,000


# ──────────────────────────────────────────────────────────────────────
# WAV Reading
# ──────────────────────────────────────────────────────────────────────

def read_wav(filepath: str) -> Tuple[np.ndarray, int]:
    """
    Read a WAV file and return (samples, sample_rate).
    Returns samples as int16 numpy array, mono.
    """
    import soundfile as sf
    audio, sr = sf.read(filepath, dtype='float32')

    # Convert to mono if stereo
    if audio.ndim > 1:
        audio = audio.mean(axis=1)

    return audio, sr


def resample(audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
    """Resample audio to target sample rate."""
    if orig_sr == target_sr:
        return audio
    import librosa
    return librosa.resample(audio, orig_sr=orig_sr, target_sr=target_sr)


def normalize_to_int16(audio: np.ndarray) -> np.ndarray:
    """Convert float32 audio to int16 range."""
    # Assume audio is in [-1.0, 1.0] range
    audio = np.clip(audio, -1.0, 1.0)
    return (audio * 32767).astype(np.int16)


def trim_or_pad(audio: np.ndarray, target_samples: int) -> np.ndarray:
    """Trim to target length or pad with silence."""
    if len(audio) > target_samples:
        audio = audio[:target_samples]
    elif len(audio) < target_samples:
        audio = np.pad(audio, (0, target_samples - len(audio)))
    return audio


# ──────────────────────────────────────────────────────────────────────
# Ring Buffer Format Conversion
# ──────────────────────────────────────────────────────────────────────

def wav_to_ringbuf(
    input_path: str,
    output_path: str,
    verbose: bool = False,
    as_c_header: bool = False,
    duration_ms: int = TARGET_DURATION_MS,
) -> bytes:
    """
    Convert a WAV file to ring buffer binary format.

    Steps:
      1. Read WAV → float32 mono
      2. Resample to 16 kHz (if needed)
      3. Trim/pad to target duration
      4. Convert float32 → int16 (matching INMP441 output range)
      5. Write raw little-endian int16 samples (no header)

    Returns the raw bytes written.
    """
    target_samples = TARGET_SAMPLE_RATE * duration_ms // 1000

    # Step 1: Read WAV
    audio, sr = read_wav(input_path)
    if verbose:
        print(f"  Input:  {input_path}")
        print(f"    Original SR: {sr} Hz, Duration: {len(audio)/sr:.3f}s, Samples: {len(audio)}")

    # Step 2: Resample
    audio = resample(audio, sr, TARGET_SAMPLE_RATE)
    if verbose and sr != TARGET_SAMPLE_RATE:
        print(f"    Resampled to: {TARGET_SAMPLE_RATE} Hz ({len(audio)} samples)")

    # Step 3: Trim/pad
    audio = trim_or_pad(audio, target_samples)
    if verbose:
        print(f"    Final: {len(audio)} samples ({len(audio)/TARGET_SAMPLE_RATE:.3f}s)")

    # Step 4: Convert to int16
    samples_i16 = normalize_to_int16(audio)

    # Step 5: Write raw bytes (little-endian int16)
    raw_bytes = samples_i16.tobytes()

    if as_c_header:
        write_c_header(output_path, samples_i16, input_path)
    else:
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(raw_bytes)

    if verbose:
        print(f"  Output: {output_path}")
        print(f"    Format: raw int16 LE, {len(raw_bytes):,} bytes ({len(raw_bytes)/1024:.2f} KB)")
        print(f"    Samples: min={samples_i16.min()}, max={samples_i16.max()}, "
              f"mean={samples_i16.mean():.1f}, std={samples_i16.std():.1f}")

    return raw_bytes


def write_c_header(output_path: str, samples: np.ndarray, source_name: str):
    """Write samples as a C header file with a byte array."""
    var_name = Path(source_name).stem.replace('-', '_').replace('.', '_')
    raw = samples.tobytes()

    lines = [
        f"/* Auto-generated from {source_name} */",
        f"/* {len(samples)} samples, int16_t, {TARGET_SAMPLE_RATE} Hz, mono */",
        f"",
        f"#ifndef TEST_AUDIO_{var_name.upper()}_H_",
        f"#define TEST_AUDIO_{var_name.upper()}_H_",
        f"",
        f"#include <stdint.h>",
        f"",
        f"#define TEST_AUDIO_{var_name.upper()}_SAMPLES {len(samples)}",
        f"#define TEST_AUDIO_{var_name.upper()}_BYTES {len(raw)}",
        f"",
        f"const int16_t test_audio_{var_name}[{len(samples)}] = {{",
    ]

    # 8 samples per line
    for i in range(0, len(samples), 8):
        chunk = samples[i:i+8]
        vals = ", ".join(f"{v:>6d}" for v in chunk)
        comma = "," if i + 8 < len(samples) else ""
        lines.append(f"    {vals}{comma}")

    lines.extend([
        f"}};",
        f"",
        f"#endif  /* TEST_AUDIO_{var_name.upper()}_H_ */",
    ])

    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    with open(output_path, 'w') as f:
        f.write("\n".join(lines) + "\n")


# ──────────────────────────────────────────────────────────────────────
# Test Signal Generation
# ──────────────────────────────────────────────────────────────────────

def generate_tone(frequency: float, output_path: str, duration_ms: int = TARGET_DURATION_MS):
    """Generate a sine wave test tone and save as ring buffer binary."""
    n_samples = TARGET_SAMPLE_RATE * duration_ms // 1000
    t = np.linspace(0, duration_ms / 1000, n_samples, endpoint=False, dtype=np.float32)
    tone = 0.5 * np.sin(2 * np.pi * frequency * t)  # 50% amplitude
    samples_i16 = normalize_to_int16(tone)

    raw_bytes = samples_i16.tobytes()
    with open(output_path, 'wb') as f:
        f.write(raw_bytes)

    print(f"Generated {frequency} Hz tone: {output_path}")
    print(f"  {n_samples} samples, {len(raw_bytes):,} bytes, {duration_ms}ms")


def generate_silence(output_path: str, duration_ms: int = TARGET_DURATION_MS):
    """Generate silence and save as ring buffer binary."""
    n_samples = TARGET_SAMPLE_RATE * duration_ms // 1000
    samples_i16 = np.zeros(n_samples, dtype=np.int16)

    raw_bytes = samples_i16.tobytes()
    with open(output_path, 'wb') as f:
        f.write(raw_bytes)

    print(f"Generated silence: {output_path}")
    print(f"  {n_samples} samples, {len(raw_bytes):,} bytes, {duration_ms}ms")


# ──────────────────────────────────────────────────────────────────────
# Ring Buffer Simulator
# ──────────────────────────────────────────────────────────────────────

class RingBufferSimulator:
    """
    Simulates the ESP32's circular ring buffer in Python.

    Use this to verify that the C firmware's ring buffer read logic
    produces the same output as reading from a .bin file directly.

    Usage:
        ring = RingBufferSimulator(capacity=16000)
        ring.write(audio_chunk)
        window = ring.read_last_n(16000)  # last 1 second
    """

    def __init__(self, capacity: int = TARGET_SAMPLES):
        self.capacity = capacity
        self.buffer = np.zeros(capacity, dtype=np.int16)
        self.write_idx = 0
        self.total_written = 0

    def write(self, data: np.ndarray):
        """Write samples into the ring buffer (circular)."""
        for sample in data:
            self.buffer[self.write_idx] = sample
            self.write_idx = (self.write_idx + 1) % self.capacity
            self.total_written += 1

    def read_last_n(self, n: int) -> np.ndarray:
        """Read the most recent n samples (matches i2s_capture_read)."""
        if n > self.capacity:
            n = self.capacity
        start = (self.write_idx + self.capacity - n) % self.capacity
        result = np.zeros(n, dtype=np.int16)
        for i in range(n):
            result[i] = self.buffer[(start + i) % self.capacity]
        return result

    def flush(self) -> np.ndarray:
        """Read the full buffer (matches i2s_capture_flush)."""
        return self.read_last_n(self.capacity)

    def load_from_file(self, filepath: str):
        """Load raw int16 samples from a .bin file into the ring buffer."""
        data = np.fromfile(filepath, dtype=np.int16)
        self.write(data)
        return len(data)

    def state_summary(self) -> str:
        return (f"RingBuffer(capacity={self.capacity}, write_idx={self.write_idx}, "
                f"total_written={self.total_written})")


# ──────────────────────────────────────────────────────────────────────
# Bit-Exact Verification
# ──────────────────────────────────────────────────────────────────────

def verify_bit_exact(wav_path: str, bin_path: str) -> bool:
    """
    Verify that a .wav → .bin conversion is bit-exact.
    Also verifies that reading from the ring buffer simulator
    produces the same samples.
    """
    # Convert WAV to ringbuf
    wav_to_ringbuf(wav_path, bin_path + ".verify", verbose=False)

    # Read both files
    with open(bin_path, 'rb') as f:
        expected = f.read()
    with open(bin_path + ".verify", 'rb') as f:
        actual = f.read()

    # Clean up
    os.remove(bin_path + ".verify")

    if expected == actual:
        print(f"  ✓ Bit-exact match: {wav_path} ↔ {bin_path}")
        return True
    else:
        print(f"  ✗ MISMATCH: {wav_path} ↔ {bin_path}")
        print(f"    Expected {len(expected)} bytes, got {len(actual)} bytes")
        return False


# ──────────────────────────────────────────────────────────────────────
# Batch Conversion
# ──────────────────────────────────────────────────────────────────────

def batch_convert(input_dir: str, output_dir: str, verbose: bool = False):
    """Convert all WAV files in a directory to ring buffer binaries."""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    wav_files = sorted(input_path.glob("*.wav"))
    if not wav_files:
        print(f"No .wav files found in {input_dir}")
        return

    print(f"Converting {len(wav_files)} WAV files...")
    print(f"  Input:  {input_dir}")
    print(f"  Output: {output_dir}")
    print()

    for wav_file in wav_files:
        bin_file = output_path / (wav_file.stem + ".bin")
        try:
            wav_to_ringbuf(str(wav_file), str(bin_file), verbose=verbose)
        except Exception as e:
            print(f"  ✗ Error: {wav_file.name}: {e}")

    print(f"\nDone. {len(wav_files)} files converted.")


# ──────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Convert WAV files to ESP32 ring buffer binary format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s input.wav output.bin
  %(prog)s input.wav output.bin --verbose
  %(prog)s input.wav test_audio.h --as-c-header
  %(prog)s --generate-tone 440 tone.bin
  %(prog)s --generate-silence silence.bin
  %(prog)s dataset/positives/ output_bins/ --batch
        """
    )
    parser.add_argument("input", nargs="?", help="Input WAV file or directory")
    parser.add_argument("output", nargs="?", help="Output .bin file or directory")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed info")
    parser.add_argument("--as-c-header", action="store_true", help="Output as C header file")
    parser.add_argument("--batch", action="store_true", help="Convert all WAVs in input directory")
    parser.add_argument("--generate-tone", type=float, metavar="FREQ",
                        help="Generate a sine wave test tone at FREQ Hz")
    parser.add_argument("--generate-silence", action="store_true", help="Generate silence")
    parser.add_argument("--duration-ms", type=int, default=1000,
                        help="Duration in ms (default: 1000)")
    parser.add_argument("--verify", type=str, metavar="BIN",
                        help="Verify WAV→BIN conversion is bit-exact")
    args = parser.parse_args()

    if args.generate_tone:
        output = args.output or f"tone_{int(args.generate_tone)}hz.bin"
        generate_tone(args.generate_tone, output, args.duration_ms)

    elif args.generate_silence:
        output = args.output or "silence.bin"
        generate_silence(output, args.duration_ms)

    elif args.batch:
        if not args.input or not args.output:
            print("Batch mode requires input directory and output directory")
            sys.exit(1)
        batch_convert(args.input, args.output, args.verbose)

    elif args.verify:
        if not args.input:
            print("Verify mode requires input WAV file")
            sys.exit(1)
        verify_bit_exact(args.input, args.verify)

    elif args.input and args.output:
        wav_to_ringbuf(args.input, args.output, args.verbose, args.as_c_header, args.duration_ms)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
