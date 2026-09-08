"""
Spectra KWS — MFCC Feature Extraction (Python Reference Implementation)

This is the reference front-end. The C implementation in firmware/main/mfcc.c
must produce bit-identical output given the same input audio.

Feature pipeline:
  1. Pre-emphasis (α = 0.97)
  2. Framing: 25 ms window, 10 ms hop  →  98 frames for 1 s of 16 kHz audio
  3. Hamming window
  4. 256-point FFT → power spectrum
  5. 40-band Mel filterbank (60–7800 Hz for 16 kHz)
  6. Log(energy) per band
  7. DCT → keep first 13 coefficients
  8. Drop c0 → keep c1–c13  (13 MFCCs per frame)
  9. Sliding window: 98 × 13 → centre-crop to 49 × 13
 10. Delta + delta-delta appended → 49 × 39 (or 49 × 10 if reduced)
 11. Normalise per-utterance (zero mean, unit variance)

Output: (49, 10) float32 tensor  —  fed to DS-CNN every 200 ms.
"""

import numpy as np
from numpy.lib.stride_tricks import as_strided
from typing import Optional, Tuple


# ──────────────────────────────────────────────────────────────────────
# Constants (match these exactly in firmware)
# ──────────────────────────────────────────────────────────────────────
SAMPLE_RATE = 16000          # Hz
FRAME_LENGTH_MS = 25         # ms
FRAME_SHIFT_MS = 10          # ms
PRE_EMPHASIS = 0.97
FFT_SIZE = 256
N_MELS = 40
MEL_LOW_HZ = 60.0
MEL_HIGH_HZ = 7800.0
N_MFCC = 13                  # keep c1..c13 (drop c0)
WINDOW_DURATION_S = 1.0      # 1 s sliding window
N_FRAMES = 49                # ceil((1000 - 25) / 10)
N_FEATURES = 10              # final feature dimension (MFCCs or MFCC+deltas)


def hz_to_mel(hz: float) -> float:
    return 2595.0 * np.log10(1.0 + hz / 700.0)


def mel_to_hz(mel: float) -> float:
    return 700.0 * (10.0 ** (mel / 2595.0) - 1.0)


def mel_filterbank(
    n_fft: int = FFT_SIZE,
    n_mels: int = N_MELS,
    sample_rate: int = SAMPLE_RATE,
    low_hz: float = MEL_LOW_HZ,
    high_hz: float = MEL_HIGH_HZ,
) -> np.ndarray:
    """Create a Mel filterbank matrix: (n_mels, n_fft//2 + 1)."""
    n_bins = n_fft // 2 + 1
    low_mel = hz_to_mel(low_hz)
    high_mel = hz_to_mel(high_hz)
    mel_points = np.linspace(low_mel, high_mel, n_mels + 2)
    hz_points = mel_to_hz(mel_points)
    bin_points = np.floor((n_fft + 1) * hz_points / sample_rate).astype(int)

    filters = np.zeros((n_mels, n_bins), dtype=np.float32)
    for m in range(n_mels):
        left = bin_points[m]
        centre = bin_points[m + 1]
        right = bin_points[m + 2]
        for k in range(left, centre):
            if centre != left:
                filters[m, k] = (k - left) / (centre - left)
        for k in range(centre, right):
            if right != centre:
                filters[m, k] = (right - k) / (right - centre)
    return filters


def pre_emphasis(signal: np.ndarray, coeff: float = PRE_EMPHASIS) -> np.ndarray:
    """Apply pre-emphasis filter: y[n] = x[n] - α * x[n-1]."""
    return np.append(signal[0], signal[1:] - coeff * signal[:-1])


def frame_signal(
    signal: np.ndarray,
    frame_length: int,
    frame_shift: int,
) -> np.ndarray:
    """Slice signal into overlapping frames using stride tricks."""
    n_frames = 1 + (len(signal) - frame_length) // frame_shift
    shape = (n_frames, frame_length)
    strides = (signal.strides[0] * frame_shift, signal.strides[0])
    return as_strided(signal, shape=shape, strides=strides).copy()


def compute_mfcc(signal: np.ndarray, sample_rate: int = SAMPLE_RATE) -> np.ndarray:
    """
    Compute MFCC features from a 1-second audio signal.

    Args:
        signal: 1-D float32 array of shape (16000,) — one second at 16 kHz.
        sample_rate: sampling rate (default 16000).

    Returns:
        mfccs: float32 array of shape (49, 10) — ready for DS-CNN.
    """
    assert len(signal) == sample_rate, f"Expected {sample_rate} samples, got {len(signal)}"

    frame_length = int(sample_rate * FRAME_LENGTH_MS / 1000)   # 400
    frame_shift = int(sample_rate * FRAME_SHIFT_MS / 1000)     # 160

    # 1. Pre-emphasis
    signal = pre_emphasis(signal)

    # 2. Framing
    frames = frame_signal(signal, frame_length, frame_shift)    # (98, 400)

    # 3. Hamming window
    window = np.hamming(frame_length).astype(np.float32)
    frames *= window

    # 4. FFT → power spectrum
    fft_result = np.fft.rfft(frames, n=FFT_SIZE)
    power = np.abs(fft_result) ** 2                            # (98, 129)

    # 5. Mel filterbank
    fbank = mel_filterbank()
    mel_energy = np.dot(power, fbank.T)                        # (98, 40)
    mel_energy = np.maximum(mel_energy, 1e-10)  # avoid log(0)

    # 6. Log energy
    log_mel = np.log(mel_energy)                               # (98, 40)

    # 7. DCT-II to get MFCCs
    from scipy.fft import dct
    mfccs = dct(log_mel, type=2, axis=1, norm='ortho')[:, :N_MFCC]  # (98, 13)

    # 8. Drop c0 (DC component) → keep c1..c13 → 13 coefficients
    # (dct already sorted low-to-high; we take columns 0..12 = c0..c12)
    # Actually, keeping all 13 including c0 for now, we'll select features below.

    # 9. Sliding window: centre-crop to 49 frames
    total_frames = mfccs.shape[0]                             # 98
    if total_frames >= N_FRAMES:
        start = (total_frames - N_FRAMES) // 2
        mfccs = mfccs[start:start + N_FRAMES]                # (49, 13)
    else:
        # Pad if needed (shouldn't happen for 1 s at 16 kHz)
        pad = np.zeros((N_FRAMES - total_frames, N_MFCC), dtype=np.float32)
        mfccs = np.concatenate([mfccs, pad], axis=0)

    # 10. Compute delta and delta-delta
    delta = compute_delta(mfccs)
    delta2 = compute_delta(delta)

    # Combine: MFCC (13) + delta (13) + delta2 (13) = 39 features
    # For the tiny model, we use a reduced set of 10 features
    # Option A: use first 10 MFCCs only (simplest, good enough for KWS)
    # Option B: use MFCC+delta with selection
    features = mfccs[:, :N_FEATURES]                          # (49, 10)

    # 11. Per-utterance normalisation
    mean = features.mean(axis=0, keepdims=True)
    std = features.std(axis=0, keepdims=True) + 1e-8
    features = (features - mean) / std

    return features.astype(np.float32)


def compute_delta(feats: np.ndarray, N: int = 2) -> np.ndarray:
    """Compute delta features using first-order central difference."""
    n_frames, n_coeffs = feats.shape
    delta = np.zeros_like(feats)
    denominator = 2.0 * sum(i ** 2 for i in range(1, N + 1))
    for t in range(n_frames):
        for n in range(1, N + 1):
            if t + n < n_frames:
                delta[t] += n * feats[t + n]
            if t - n >= 0:
                delta[t] -= n * feats[t - n]
        delta[t] /= denominator
    return delta


def extract_features_from_file(
    filepath: str,
    target_sr: int = SAMPLE_RATE,
) -> np.ndarray:
    """Load a WAV file and extract (49, 10) MFCC features."""
    import soundfile as sf
    audio, sr = sf.read(filepath, dtype='float32')
    if audio.ndim > 1:
        audio = audio.mean(axis=1)  # mono
    if sr != target_sr:
        import librosa
        audio = librosa.resample(audio, orig_sr=sr, target_sr=target_sr)
    # Trim or pad to exactly 1 second
    target_len = target_sr
    if len(audio) > target_len:
        audio = audio[:target_len]
    elif len(audio) < target_len:
        audio = np.pad(audio, (0, target_len - len(audio)))
    return compute_mfcc(audio)


# ──────────────────────────────────────────────────────────────────────
# CLI — test feature extraction on a single file
# ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python features.py <audio.wav>")
        sys.exit(1)

    feats = extract_features_from_file(sys.argv[1])
    print(f"Features shape: {feats.shape}")
    print(f"Features dtype: {feats.dtype}")
    print(f"Mean: {feats.mean():.4f}, Std: {feats.std():.4f}")
    print(f"Min: {feats.min():.4f}, Max: {feats.max():.4f}")
    print(f"\nFirst frame:\n{feats[0]}")
