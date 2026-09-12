"""Shared processing core: ASR -> verification -> intent. Used by REST, WS and MQTT."""
from __future__ import annotations

import time

import numpy as np

from .asr_worker import ASRWorker
from .co_verifier import CoVerifier
from .intent_router import IntentRouter


class AgniPipeline:
    def __init__(self, cfg: dict):
        a = cfg["asr"]
        self.asr = ASRWorker(model_size=a["model_size"], device=a["device"],
                             compute_type=a["compute_type"], beam_size=a["beam_size"],
                             language=a["language"], vad_filter=a["vad_filter"],
                             no_speech_threshold=a["no_speech_threshold"])
        v = cfg["verifier"]
        self.verifier = CoVerifier(model_path=v["edge_model_path"] if v["enabled"] else None,
                                   cosine_threshold=v["cosine_threshold"],
                                   wake_span_end_s=v["wake_span_end_s"],
                                   degraded=v["vfs_degraded"])
        self.router = IntentRouter(cfg["intent"]["grammar_path"],
                                   freeform_fallback=cfg["intent"]["freeform_fallback"])

    def process(self, audio: np.ndarray, prototype=None, keyword=None,
                language: str | None = None) -> dict:
        t0 = time.perf_counter()
        t = self.asr.transcribe(audio, language=language)
        verification = (self.verifier.verify(audio, prototype)
                        if prototype else {"verified": None, "cosine": None,
                                           "note": "no prototype in payload"})
        intent = None
        # Gate 1: empty / low-confidence transcripts never reach actuators
        if t.text and t.avg_no_speech < self.asr.no_speech_threshold:
            intent = self.router.parse(t.text)
            intent["wake_keyword"] = keyword
            # Gate 2: explicit cloud-side veto — transcript produced but blocked
            if verification.get("verified") is False and intent["type"] == "command":
                intent = {"type": "blocked", "raw": t.text,
                          "note": "co-verifier veto: wake-word mismatch"}
        return {
            "transcript": t.text,
            "language": t.language,
            "intent": intent,
            "verification": verification,
            "segments": t.segments,
            "timing": {"asr_ms": t.asr_ms,
                       "total_ms": int((time.perf_counter() - t0) * 1000),
                       "audio_s": t.duration_s},
            "model": {"name": self.asr.model_size, "device": self.asr.device},
        }
