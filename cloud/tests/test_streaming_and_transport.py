"""Partial-decoder VAD orchestration + FLAC transport round-trip."""
import numpy as np
import pytest

from serving.audio_utils import float_to_flac, load_any
from serving.partial_decoder import PartialDecoder


def _chunks(n=10, amp=0.05, n_sil=8):
    speech = [np.full(1600, amp, np.float32) for _ in range(n)]
    sil = [np.full(1600, 1e-4, np.float32) for _ in range(n_sil)]
    return speech + sil


def test_partial_then_silence_final():
    calls = []
    dec = PartialDecoder(decode_fn=lambda buf: calls.append(len(buf)) or "text",
                         partial_every_s=0.1, silence_ms=200)
    events = [ev for c in _chunks() for ev in dec.push(c)]
    types = [e["type"] for e in events]
    assert "partial" in types
    assert events[-1]["type"] == "final" and events[-1]["reason"] == "silence"
    assert len(calls) >= 2                                # re-decode cadence works


def test_no_decoder_final_on_flush():
    dec = PartialDecoder(decode_fn=None)
    for c in _chunks(n=3, n_sil=0):
        dec.push(c)
    fin = dec.finalize()
    assert fin["type"] == "final" and fin["text"] == ""
    assert dec.finalize() is None                         # buffer cleared


def test_progress_partials_without_decoder():
    dec = PartialDecoder(decode_fn=None, partial_every_s=0.1)
    events = [ev for c in _chunks(n=6, n_sil=0) for ev in dec.push(c)]
    partials = [e for e in events if e["type"] == "partial"]
    assert partials, "expected progress partials even without command model"
    assert all(p["text"] is None for p in partials)


def test_maxlen_forces_final():
    dec = PartialDecoder(decode_fn=lambda b: "x", max_utt_s=0.5)
    events = [ev for c in _chunks(n=6, n_sil=0) for ev in dec.push(c)]
    assert any(e["type"] == "final" and e["reason"] == "maxlen" for e in events)


def test_flac_roundtrip():
    sr = 16000
    t = np.arange(2 * sr) / sr
    x = (0.45 * np.sin(2 * np.pi * 440 * t) +
         0.20 * np.sin(2 * np.pi * 1170 * t)).astype(np.float32)  # legal [-1,1] speech-ish
    b = float_to_flac(x)
    assert 0.25 * len(x) * 2 < len(b) < 0.85 * len(x) * 2  # compression on harmonics
    y = load_any(b, "flac")
    assert len(y) == len(x)
    assert np.max(np.abs(x - y)) < 1e-4                   # lossless within int16 grid


def test_opus_guard_or_roundtrip():
    try:
        import opuslib  # noqa: F401
    except ImportError:
        with pytest.raises(RuntimeError, match="opuslib"):
            load_any(b"", "opus")
        return
    x = np.zeros(3200, np.float32)
    from serving.audio_utils import opus_encode
    y = load_any(opus_encode(x), "opus")
    assert y.size == 3200
