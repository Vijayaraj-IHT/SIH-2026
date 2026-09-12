"""Audio ingress utilities: bytes -> float32 mono 16 kHz numpy for ASR/verifier.

The ESP32 handover payload is raw little-endian PCM16 @ 16 kHz (matches
`audio.sample_rate: 16000` in configs/config.yaml of the edge repo). WAV and
arbitrary sample rates are also accepted for PC-side testing.
"""
from __future__ import annotations

import base64
import io

import numpy as np

TARGET_SR = 16000


def pcm16_bytes_to_float(raw: bytes) -> np.ndarray:
    """Little-endian int16 PCM -> float32 in [-1, 1]."""
    x = np.frombuffer(raw, dtype="<i2")
    return x.astype(np.float32) / 32768.0


def b64_to_float(b64: str) -> np.ndarray:
    return pcm16_bytes_to_float(base64.b64decode(b64))


def wav_bytes_to_float(buf: bytes) -> tuple[np.ndarray, int]:
    """Decode a WAV container -> (float32 mono, sample_rate)."""
    import soundfile as sf  # local import: keeps module light for tests

    data, sr = sf.read(io.BytesIO(buf), dtype="float32", always_2d=True)
    mono = data.mean(axis=1)
    return mono, int(sr)


def resample_to_16k(audio: np.ndarray, sr: int) -> np.ndarray:
    """Polyphase-quality resample via numpy linear interp (demo-grade, 0 deps).

    Production path: always send 16 kHz from the ESP32 so this is a no-op.
    """
    if sr == TARGET_SR or audio.size == 0:
        return audio.astype(np.float32, copy=False)
    ratio = TARGET_SR / sr
    n_out = int(round(audio.size * ratio))
    xp = np.arange(audio.size)
    x = np.linspace(0, audio.size - 1, n_out)
    return np.interp(x, xp, audio).astype(np.float32)


def clamp_duration(audio: np.ndarray, max_s: float, sr: int = TARGET_SR) -> np.ndarray:
    return audio[: int(max_s * sr)] if audio.size > int(max_s * sr) else audio


def rms_db(audio: np.ndarray) -> float:
    """For logging / diagnostics (mirrors the live-mic volume meter UX)."""
    if audio.size == 0:
        return -120.0
    rms = float(np.sqrt(np.mean(np.square(audio))) + 1e-12)
    return 20.0 * np.log10(rms + 1e-12)


def float_to_flac(audio: np.ndarray, sr: int = TARGET_SR) -> bytes:
    """Lossless, zero-dependency compression — ~50% of PCM16 (Session 3 default)."""
    import soundfile as sf
    buf = io.BytesIO()
    sf.write(buf, np.clip(audio, -1, 1), sr, format="FLAC", subtype="PCM_16")
    return buf.getvalue()


def opus_encode(audio: np.ndarray, sr: int = TARGET_SR, bitrate: int = 24000) -> bytes:
    """Optional lossy path for bandwidth-tight links (needs `pip install opuslib`)."""
    try:
        import opuslib
    except ImportError as e:
        raise RuntimeError("opus needs libopus + `pip install opuslib`") from e
    if sr != TARGET_SR:
        raise ValueError("opus path expects 16 kHz input")
    enc = opuslib.Encoder(TARGET_SR, 1, opuslib.APPLICATION_AUDIO)
    enc.bitrate = bitrate
    x = (np.clip(audio, -1, 1) * 32767).astype("<i2")
    out = bytearray()
    for i in range(0, len(x), 960):                      # 60 ms frames
        frame = x[i:i + 960]
        if len(frame) < 960:
            frame = np.pad(frame, (0, 960 - len(frame)))
        out += enc.encode(frame.tobytes(), 960)
    return bytes(out)


def opus_decode(payload: bytes) -> np.ndarray:
    try:
        import opuslib
    except ImportError as e:
        raise RuntimeError("opus needs libopus + `pip install opuslib`") from e
    dec = opuslib.Decoder(TARGET_SR, 1)
    out = np.zeros(0, np.int16)
    for i in range(0, len(payload), 60):                 # ~30 B per 60 ms frame
        frame = dec.decode(payload[i:i + 60], 960, decode_fec=False)
        out = np.concatenate([out, np.frombuffer(frame, dtype="<i2")])
    return out.astype(np.float32) / 32768.0


def load_any(audio: bytes, fmt: str, sr: int = TARGET_SR) -> np.ndarray:
    """Unified ingress router.

    fmt: 'pcm16' (raw, little-endian, 16 kHz) | 'wav' | 'flac' | 'opus'
    """
    if fmt == "wav":
        a, in_sr = wav_bytes_to_float(audio)
        return resample_to_16k(a, in_sr)
    if fmt == "pcm16":
        return pcm16_bytes_to_float(audio)
    if fmt == "flac":
        a, in_sr = wav_bytes_to_float(audio)             # soundfile handles FLAC
        return resample_to_16k(a, in_sr)
    if fmt == "opus":
        return opus_decode(audio)
    raise ValueError(f"unsupported audio format '{fmt}' (supported: pcm16, wav, flac, opus)")
