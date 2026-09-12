"""Streaming orchestration for /ws/asr: energy-VAD windowing + partial/final events.

The command model is so small that re-decoding the held utterance every
~400 ms costs milliseconds — genuine partial transcripts without a complex
streaming architecture ("decode-then-redecode" trick used by product ASRs).
The heavy Whisper path stays reserved for the FINAL full-quality transcript.
"""
from __future__ import annotations

import numpy as np


class PartialDecoder:
    def __init__(self, decode_fn=None, sr: int = 16000,
                 partial_every_s: float = 0.40, silence_ms: int = 600,
                 rms_active: float = 0.010, rms_end: float = 0.006,
                 max_utt_s: float = 8.0):
        self.decode_fn = decode_fn
        self.sr, self.every = sr, int(partial_every_s * sr)
        self.sil_n = int(silence_ms / 1000 * sr)
        self.rms_active, self.rms_end = rms_active, rms_end
        self.max_n = int(max_utt_s * sr)
        self.reset()

    def reset(self):
        self.buf = np.zeros(0, np.float32)
        self.speech = False
        self.trailing_sil = 0
        self.since_partial = 0

    # ------------------------------------------------------------------ core
    def push(self, chunk: np.ndarray) -> list[dict]:
        events: list[dict] = []
        if chunk.size == 0:
            return events
        self.buf = np.concatenate([self.buf, chunk.astype(np.float32)])
        rms = float(np.sqrt(np.mean(np.square(chunk))) + 1e-12)
        if rms > self.rms_active:
            self.speech, self.trailing_sil = True, 0
        elif rms < self.rms_end:
            self.trailing_sil += chunk.size
        self.since_partial += chunk.size

        if self.speech and self.since_partial >= self.every:
            text = self.decode_fn(self.buf) if self.decode_fn else None
            events.append({"type": "partial", "text": text,
                           "audio_s": round(self.buf.size / self.sr, 3),
                           "note": None if self.decode_fn else "command model disabled — progress only"})
            self.since_partial = 0
        if self.buf.size >= self.max_n:
            events.append(self._final("maxlen"))
        elif self.speech and self.trailing_sil >= self.sil_n:
            events.append(self._final("silence"))
        return events

    def finalize(self) -> dict | None:
        return self._final("flush") if self.buf.size else None

    def _final(self, reason: str) -> dict:
        text = self.decode_fn(self.buf) if (self.decode_fn and self.speech) else ""
        ev = {"type": "final", "text": text, "reason": reason,
              "audio_s": round(self.buf.size / self.sr, 3)}
        self.reset()
        return ev
