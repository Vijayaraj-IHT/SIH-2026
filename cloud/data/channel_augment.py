"""ESP32-channel-matched augmentation chain (implements plan §5).

      speed perturb ─> noise @ SNR ─> RIR convolve ─> bandpass 100 Hz–7.6 kHz
                    └─ int16 quantize └─ gain jitter

RIRs are generated procedurally (exponentially-decaying noise, RT60-controlled)
so no RIR downloads are needed; swap `load_rir_dir()` in when real room IRs
(OpenAIR / BUT Speech@FIT) are available on the VM. All ops are deterministic
given a numpy Generator — the training recipe and tests depend on it.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from scipy.signal import butter, sosfilt

_SR = 16000


# --------------------------------------------------------------------- atoms
def speed_perturb(x: np.ndarray, factor: float) -> np.ndarray:
    if abs(factor - 1.0) < 1e-3 or x.size == 0:
        return x.astype(np.float32, copy=False)
    n = int(round(x.size / factor))
    xp = np.arange(x.size)
    return np.interp(np.linspace(0, x.size - 1, n), xp, x).astype(np.float32)


def add_noise(x: np.ndarray, noise: np.ndarray, snr_db: float,
              rng: np.random.Generator) -> np.ndarray:
    """Mix at exact SNR measured on average power; noise is looped/tiled."""
    if noise.size == 0 or x.size == 0:
        return x
    if noise.size < x.size:
        reps = int(np.ceil(x.size / noise.size))
        noise = np.tile(noise, reps)
    start = int(rng.integers(0, max(1, noise.size - x.size)))
    seg = noise[start:start + x.size]
    sig_p = np.mean(x ** 2) + 1e-12
    noi_p = np.mean(seg ** 2) + 1e-12
    seg = seg * np.sqrt(sig_p / (10 ** (snr_db / 10) * noi_p))
    return (x + seg).astype(np.float32)


def make_rir(rt60: float = 0.35, sr: int = _SR,
             rng: np.random.Generator | None = None) -> np.ndarray:
    """Procedural exponentially-decaying RIR with a 3 ms direct path."""
    rng = rng or np.random.default_rng(0)
    n = int(rt60 * sr * 1.2) + int(0.003 * sr) + 8
    t = np.arange(n) / sr
    rir = 0.15 * rng.standard_normal(n) * np.exp(-6.91 * t / rt60)
    rir[: int(0.002 * sr)] = 0.0
    rir[int(0.003 * sr)] += 1.0                       # direct path DOMINATES (~13 dB over tail)
    return (rir / (np.linalg.norm(rir) + 1e-12)).astype(np.float32)


def convolve_rir(x: np.ndarray, rir: np.ndarray) -> np.ndarray:
    y = np.convolve(x, rir, mode="full")[: x.size]
    return y.astype(np.float32)


def bandpass_channel(x: np.ndarray, sr: int = _SR,
                     low: float = 100.0, high: float = 7600.0) -> np.ndarray:
    sos = butter(4, [low, high], btype="band", fs=sr, output="sos")
    return sosfilt(sos, x).astype(np.float32)


def quantize_int16(x: np.ndarray) -> np.ndarray:
    return (np.clip(x, -1.0, 1.0) * 32767.0).round().astype(np.int16).astype(np.float32) / 32767.0


def gain_jitter(x: np.ndarray, db: float) -> np.ndarray:
    return np.clip(x * float(10 ** (db / 20.0)), -1.0, 1.0).astype(np.float32)


# --------------------------------------------------------------------- chain
@dataclass
class ChannelAug:
    speed_p: float = 0.30
    speed_factors: tuple = (0.9, 1.1)
    noise_p: float = 0.50
    snr_choices: tuple = (0, 5, 10, 15, 20, 30)
    rir_p: float = 0.30
    rt60_range: tuple = (0.15, 0.60)
    bandpass_p: float = 0.50
    gain_p: float = 0.50
    gain_db_range: tuple = (-6.0, 3.0)
    quantize: bool = True
    noise_pool: list = field(default_factory=list)  # list of np.ndarray @16kHz

    def __call__(self, x: np.ndarray, rng: np.random.Generator) -> np.ndarray:
        x = x.astype(np.float32, copy=False)
        if rng.random() < self.speed_p:
            x = speed_perturb(x, float(rng.choice(self.speed_factors)))
        if self.noise_pool and rng.random() < self.noise_p:
            x = add_noise(x, self.noise_pool[int(rng.integers(len(self.noise_pool)))],
                          float(rng.choice(self.snr_choices)), rng)
        if rng.random() < self.rir_p:
            x = convolve_rir(x, make_rir(float(rng.uniform(*self.rt60_range)), rng=rng))
        if rng.random() < self.bandpass_p:
            x = bandpass_channel(x)
        if rng.random() < self.gain_p:
            x = gain_jitter(x, float(rng.uniform(*self.gain_db_range)))
        return quantize_int16(x) if self.quantize else x


def load_noise_pool(noise_dir: str | Path, max_files: int = 400,
                    min_s: float = 1.0) -> list:
    """Read MUSAN-style wav tree into a pool of float32 mono 16 kHz arrays."""
    import soundfile as sf
    pool = []
    for p in sorted(Path(noise_dir).rglob("*.wav"))[:max_files]:
        try:
            d, sr = sf.read(str(p), dtype="float32", always_2d=True)
            mono = d.mean(axis=1)
            if sr != _SR:
                mono = speed_perturb(mono, sr / _SR)          # resample as ratio
            if mono.size >= min_s * _SR:
                pool.append(mono.astype(np.float32))
        except Exception:
            continue
    return pool
