"""
Spectra KWS — Audio Augmentation Pipeline

Augmentation strategies to make the model robust in real-world conditions:

1. Noise mixing — overlay background noise at random SNR (5–20 dB)
2. Time shift — ±200 ms circular shift
3. Gain perturbation — ±6 dB random gain
4. Speed perturbation — 0.9×–1.1× speed (resample)
5. Room simulation — simple reverb via exponential decay convolution
6. TTS augmentation — synthesised "Spectra" utterances for extra positives

These mirror the augmentation pipeline described in:
  - Alexa KWS paper
  - arXiv 2011.01460
"""

import numpy as np
from typing import List, Optional, Tuple
from pathlib import Path


def load_audio(filepath: str, target_sr: int = 16000) -> np.ndarray:
    """Load a WAV file as mono float32."""
    import soundfile as sf
    audio, sr = sf.read(filepath, dtype='float32')
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    if sr != target_sr:
        import librosa
        audio = librosa.resample(audio, orig_sr=sr, target_sr=target_sr)
    return audio


def add_noise(
    audio: np.ndarray,
    noise: np.ndarray,
    snr_db: float = 10.0,
) -> np.ndarray:
    """
    Mix noise into audio at a given SNR.

    Args:
        audio: clean signal
        noise: noise signal (will be looped/truncated to match audio length)
        snr_db: signal-to-noise ratio in dB
    """
    # Match noise length to audio
    if len(noise) < len(audio):
        loops = (len(audio) // len(noise)) + 1
        noise = np.tile(noise, loops)
    noise = noise[:len(audio)]

    # Compute scaling factor
    audio_power = np.mean(audio ** 2) + 1e-10
    noise_power = np.mean(noise ** 2) + 1e-10
    snr_linear = 10 ** (snr_db / 20.0)
    noise_scale = np.sqrt(audio_power / (noise_power * snr_linear ** 2))

    return (audio + noise * noise_scale).astype(np.float32)


def time_shift(audio: np.ndarray, max_shift_ms: int = 200, sr: int = 16000) -> np.ndarray:
    """Circular time shift by a random amount in [-max_shift_ms, +max_shift_ms]."""
    max_shift_samples = int(max_shift_ms * sr / 1000)
    shift = np.random.randint(-max_shift_samples, max_shift_samples + 1)
    return np.roll(audio, shift).astype(np.float32)


def gain_perturbation(audio: np.ndarray, max_db: float = 6.0) -> np.ndarray:
    """Random gain change in [-max_db, +max_db] dB."""
    gain_db = np.random.uniform(-max_db, max_db)
    gain_linear = 10 ** (gain_db / 20.0)
    return (audio * gain_linear).astype(np.float32)


def speed_perturbation(
    audio: np.ndarray,
    speed_range: Tuple[float, float] = (0.9, 1.1),
    sr: int = 16000,
) -> np.ndarray:
    """
    Speed perturbation by resampling.
    Changes both speed and pitch (natural variation).
    """
    import librosa
    speed = np.random.uniform(*speed_range)
    n_target = int(len(audio) / speed)
    augmented = librosa.resample(audio, orig_sr=sr, target_sr=int(sr * speed))
    # Trim or pad back to original length
    if len(augmented) > len(audio):
        augmented = augmented[:len(audio)]
    elif len(augmented) < len(audio):
        augmented = np.pad(augmented, (0, len(audio) - len(augmented)))
    return augmented.astype(np.float32)


def simple_reverb(
    audio: np.ndarray,
    rt60_ms: float = 100.0,
    sr: int = 16000,
) -> np.ndarray:
    """
    Simple exponential-decay reverb simulation.
    RT60 = time for 60 dB decay.
    """
    decay_samples = int(rt60_ms * sr / 1000)
    ir = np.exp(-6.9 * np.arange(decay_samples) / decay_samples).astype(np.float32)
    reverb = np.convolve(audio, ir, mode='full')[:len(audio)]
    # Mix dry + wet
    mix = 0.7 * audio + 0.3 * reverb
    return mix.astype(np.float32)


def augment_sample(
    audio: np.ndarray,
    noise_files: Optional[List[str]] = None,
    sr: int = 16000,
) -> np.ndarray:
    """
    Apply a random combination of augmentations.

    Args:
        audio: input audio (1 s, 16 kHz)
        noise_files: list of paths to background noise WAV files
        sr: sampling rate
    Returns:
        augmented audio
    """
    result = audio.copy()

    # Random time shift (50% chance)
    if np.random.random() < 0.5:
        result = time_shift(result, sr=sr)

    # Random gain (70% chance)
    if np.random.random() < 0.7:
        result = gain_perturbation(result)

    # Random speed perturbation (30% chance)
    if np.random.random() < 0.3:
        result = speed_perturbation(result, sr=sr)

    # Random noise mixing (60% chance)
    if noise_files and np.random.random() < 0.6:
        noise_path = np.random.choice(noise_files)
        noise = load_audio(noise_path, target_sr=sr)
        snr_db = np.random.uniform(5.0, 20.0)
        result = add_noise(result, noise, snr_db=snr_db)

    # Random reverb (20% chance)
    if np.random.random() < 0.2:
        result = simple_reverb(result)

    # Clip to prevent overflow
    result = np.clip(result, -1.0, 1.0)
    return result


def augment_batch(
    audio: np.ndarray,
    n_augmentations: int = 3,
    noise_files: Optional[List[str]] = None,
    sr: int = 16000,
) -> List[np.ndarray]:
    """
    Generate multiple augmented versions of a single audio sample.

    Returns list of augmented samples (original NOT included).
    """
    return [augment_sample(audio, noise_files, sr) for _ in range(n_augmentations)]


# ──────────────────────────────────────────────────────────────────────
# CLI — test augmentation on a single file
# ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    import soundfile as sf

    if len(sys.argv) < 2:
        print("Usage: python augmentation.py <audio.wav> [output_dir]")
        sys.exit(1)

    audio = load_audio(sys.argv[1])
    outdir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(".")
    outdir.mkdir(parents=True, exist_ok=True)

    noise_dir = Path("dataset/background")
    noise_files = [str(f) for f in noise_dir.glob("*.wav")] if noise_dir.exists() else None

    augmented = augment_batch(audio, n_augmentations=5, noise_files=noise_files)

    for i, aug in enumerate(augmented):
        out_path = outdir / f"aug_{i:02d}.wav"
        sf.write(str(out_path), aug, 16000)
        print(f"Saved: {out_path}")
