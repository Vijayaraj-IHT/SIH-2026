"""Shared character vocabulary for the CTC command model (Session 3).

Index 0 is always the CTC blank. Kept deliberately tiny: command-domain speech
needs letters, digits, space and apostrophe — nothing else.
"""
from __future__ import annotations

import re

BLANK_ID = 0
_CHARS = list("abcdefghijklmnopqrstuvwxyz '0123456789")
VOCAB = ["<blank>"] + _CHARS
IDX = {c: i + 1 for i, c in enumerate(_CHARS)}
V = len(VOCAB)  # = 1 blank + 26 letters + 1 space + 1 apostrophe + 10 digits = 39


def encode(text: str) -> list[int]:
    """'read telemetry 5' -> [17, 4, 0(blank filtered)...] dropping unknown chars."""
    t = re.sub(r"\s+", " ", text.lower().strip())
    return [IDX[c] for c in t if c in IDX]


def decode(ids) -> str:
    """CTC greedy: collapse repeats, strip blanks, tidy spaces."""
    out, prev = [], None
    for i in ids:
        i = int(i)
        if i != BLANK_ID and i != prev:
            out.append(VOCAB[i])
        prev = i
    return re.sub(r"\s+", " ", "".join(out)).strip()
