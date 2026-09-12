"""Model B wrapper — faster-whisper (CTranslate2) zero-shot ASR.

Session 1: zero-shot `base`/`small`. Session 2: this class transparently loads
our fine-tuned checkpoint instead (no gateway changes needed — swap model_size
for the HF repo id or local path of the fine-tuned model).
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

import numpy as np


@dataclass
class Transcription:
    text: str
    language: str
    duration_s: float
    segments: list = field(default_factory=list)
    avg_no_speech: float = 0.0
    avg_logprob: float = 0.0
    asr_ms: int = 0


class ASRWorker:
    def __init__(self, model_size: str = "base", device: str = "auto",
                 compute_type: str = "auto", beam_size: int = 5,
                 language: str | None = "en", vad_filter: bool = True,
                 no_speech_threshold: float = 0.6):
        from faster_whisper import WhisperModel  # heavy import kept lazy

        self.model_size, self.language = model_size, language
        self.beam_size, self.vad_filter = beam_size, vad_filter
        self.no_speech_threshold = no_speech_threshold
        t0 = time.perf_counter()
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        self.device = getattr(self.model.model, "device", device)
        self.load_ms = int((time.perf_counter() - t0) * 1000)

    def transcribe(self, audio: np.ndarray, language: str | None = None) -> Transcription:
        t0 = time.perf_counter()
        segments, info = self.model.transcribe(
            audio.astype(np.float32, copy=False),
            beam_size=self.beam_size,
            vad_filter=self.vad_filter,
            language=language or self.language,
            no_speech_threshold=self.no_speech_threshold,
        )
        segs = [{
            "start": round(s.start, 3), "end": round(s.end, 3),
            "text": s.text.strip(),
            "avg_logprob": round(s.avg_logprob, 4),
            "no_speech_prob": round(s.no_speech_prob, 4),
        } for s in segments]
        text = " ".join(s["text"] for s in segs).strip()
        asr_ms = int((time.perf_counter() - t0) * 1000)
        return Transcription(
            text=text,
            language=getattr(info, "language", language or self.language or "auto"),
            duration_s=round(getattr(info, "duration", 0.0), 3),
            segments=segs,
            avg_no_speech=float(np.mean([s["no_speech_prob"] for s in segs])) if segs else 1.0,
            avg_logprob=float(np.mean([s["avg_logprob"] for s in segs])) if segs else 0.0,
            asr_ms=asr_ms,
        )
