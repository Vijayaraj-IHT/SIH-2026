"""Model C — wake-word co-verification (SIH-26172 differentiator).

Idea: the edge ESP32 fires on a 32-D hypersphere prototype. The cloud re-embeds
the *wake portion* of the handover payload with the SAME frozen INT8 encoder
(models/tflite/voice_activator_int8.tflite) and vetoes when the cloud-side
cosine similarity is implausibly low — killing TV speech / confuser false
activations that the edge could not see. Cost: ~40 ms of CPU.

If tflite_runtime / TensorFlow is unavailable (e.g. tiny docker images), the
verifier degrades per config verifer.vfs_degraded policy instead of crashing.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np

# MFCC config mirrored EXACTLY from edge configs/config.yaml
_SR, N_FFT, HOP, WIN, N_MELS, N_MFCC = 16000, 512, 160, 480, 40, 13
_FRAMES = 98  # 1 s window -> 98 frames x 13 coeffs (matches edge feature grid)


def _mel_filters() -> np.ndarray:
    fmin, fmax = 20.0, _SR / 2

    def hz2mel(f): return 2595.0 * math.log10(1 + f / 700.0)
    def mel2hz(m): return 700.0 * (10 ** (m / 2595.0) - 1)

    mels = np.linspace(hz2mel(fmin), hz2mel(fmax), N_MELS + 2)
    bins = np.floor((N_FFT + 1) * mel2hz(mels) / _SR).astype(int)
    fb = np.zeros((N_MELS, N_FFT // 2 + 1), dtype=np.float32)
    for i in range(N_MELS):
        l, c, r = bins[i], bins[i + 1], bins[i + 2]
        if c > l:
            fb[i, l:c] = np.linspace(0, 1, c - l, endpoint=False)
        if r > c:
            fb[i, c:r] = np.linspace(1, 0, r - c, endpoint=False)
    return fb


def mfcc_98x13(audio: np.ndarray) -> np.ndarray:
    """1.0 s mono 16 kHz -> (98, 13) float32 MFCC, matching the edge extractor."""
    if audio.size < 16000:
        audio = np.pad(audio, (0, 16000 - audio.size))
    audio = audio[:16000]
    n_frames = 1 + (16000 - WIN) // HOP
    frames = np.stack([audio[i * HOP: i * HOP + WIN] * np.hanning(WIN) for i in range(n_frames)])
    spec = np.abs(np.fft.rfft(frames, n=N_FFT)) ** 2
    logmel = np.log(np.maximum(spec @ _mel_filters().T, 1e-10))
    n = np.arange(N_MELS) + 0.5                       # DCT-II basis (N_MELS, N_MFCC)
    k = np.arange(N_MFCC)
    dct = np.cos(np.pi / N_MELS * np.outer(n, k)).astype(np.float32)
    mfcc = logmel @ dct                               # (frames, 13)
    mfcc = mfcc[:_FRAMES]
    if mfcc.shape[0] < _FRAMES:
        mfcc = np.pad(mfcc, ((0, _FRAMES - mfcc.shape[0]), (0, 0)))
    return mfcc.astype(np.float32)[..., np.newaxis]  # (98, 13, 1)


class CoVerifier:
    def __init__(self, model_path: str | None, cosine_threshold: float = 0.70,
                 wake_span_end_s: float = 1.0, degraded: str = "warn"):
        self.threshold, self.wake_span_end_s, self.degraded = cosine_threshold, wake_span_end_s, degraded
        self.interp = None
        self.reason = None
        if not model_path or not Path(model_path).exists():
            self.reason = f"edge model not found at {model_path}"
            return
        Interpreter = None
        for modpath in ("tflite_runtime.interpreter", "ai_edge_litert.interpreter",
                        "tensorflow.lite"):
            try:
                mod = __import__(modpath, fromlist=["Interpreter"])
                Interpreter = getattr(mod, "Interpreter")
                break
            except (ImportError, AttributeError):
                continue
        if Interpreter is None:
            self.reason = ("no tflite runtime installed (tflite-runtime | "
                           "ai-edge-litert | tensorflow)")
            return
        self.interp = Interpreter(model_path=str(model_path))
        self.interp.allocate_tensors()
        self.in_det = self.interp.get_input_details()[0]
        self.out_det = self.interp.get_output_details()[0]

    @property
    def available(self) -> bool:
        return self.interp is not None

    def embed(self, audio: np.ndarray) -> np.ndarray:
        """-> L2-normalized 32-D embedding on S^31 (must match edge behavior)."""
        x = mfcc_98x13(audio)[np.newaxis]
        scale, zero = self.in_det["quantization"]
        xq = (x / scale + zero).astype(self.in_det["dtype"]) if scale > 0 else x.astype(self.in_det["dtype"])
        self.interp.set_tensor(self.in_det["index"], xq)
        self.interp.invoke()
        z = self.interp.get_tensor(self.out_det["index"]).astype(np.float32).flatten()
        zs, zz = self.out_det["quantization"]
        if zs and zs > 0:
            z = (z - zz) * zs
        return z / (np.linalg.norm(z) + 1e-12)

    def verify(self, audio_16k: np.ndarray, prototype: list[float]) -> dict:
        """Compare prototype (shipped in payload, 32 floats) vs wake portion."""
        p = np.asarray(prototype, dtype=np.float32)
        if p.shape[0] != 32 or not (0.97 < np.linalg.norm(p) < 1.03):
            return {"verified": None, "cosine": None,
                    "note": "prototype missing/invalid shape or norm"}
        wake = audio_16k[: int(self.wake_span_end_s * 16000)]
        if not self.available:
            policy = "REFUSED" if self.degraded == "refuse" else "SKIPPED"
            return {"verified": None if self.degraded == "warn" else False,
                    "cosine": None, "note": f"verifier {policy}: {self.reason}"}
        z = self.embed(wake)
        cos = float(np.dot(p / (np.linalg.norm(p) + 1e-12), z))
        return {"verified": bool(cos >= self.threshold), "cosine": round(cos, 4),
                "threshold": self.threshold}
