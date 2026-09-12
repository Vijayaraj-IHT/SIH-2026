"""Command model worker — Conformer-CTC + grammar-constrained decode (fast path).

Loaded lazily by the gateway when configs/cloud.yaml -> command_model.enabled.
Without a checkpoint (pre-training) it still runs and demonstrates the grammar
floor, printing a loud warning — serving must never crash waiting for artifacts.
"""
from __future__ import annotations

import logging
import time
from pathlib import Path

import numpy as np

from .char_vocab import decode as greedy_text
from .grammar_decoder import ConstrainedDecoder, GrammarDFA

log = logging.getLogger("agni.command")


class CommandWorker:
    def __init__(self, ckpt_path: str | None, grammar_path: str,
                 device: str = "cpu", use_grammar: bool = True):
        from .ctc_model import load_checkpoint, build_finetune_model
        self.device = device
        if ckpt_path and Path(ckpt_path).exists():
            self.model = load_checkpoint(ckpt_path, map_location=device)
            self.trained = True
        else:
            self.model = build_finetune_model()
            self.trained = False
            log.warning("command model has NO checkpoint — demoing the grammar "
                        "floor only; train with training/train_conformer_ctc.py")
        self.dfa = GrammarDFA.from_grammar(grammar_path) if use_grammar else None
        self.constrained = ConstrainedDecoder(self.dfa) if self.dfa else None

    def decode(self, audio: np.ndarray, force_greedy: bool = False) -> dict:
        from .ctc_model import decode_logits
        t0 = time.perf_counter()
        ids, logits = decode_logits(self.model, audio)
        ms = int((time.perf_counter() - t0) * 1000)
        out = {"greedy": greedy_text(ids), "latency_ms": ms, "trained": self.trained}
        if self.constrained and not force_greedy:
            import torch
            logp = torch.log_softmax(logits, dim=-1).cpu().numpy()
            c = self.constrained.decode(logp)
            out.update(text=c["text"] if c["matched"] else out["greedy"],
                       engine="ctc-grammar" if c["matched"] else "ctc-greedy",
                       grammar_matched=c["matched"], mean_margin=round(c["mean_margin"], 4))
        else:
            out.update(text=out["greedy"], engine="ctc-greedy",
                       grammar_matched=None)
        return out
