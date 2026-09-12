"""Grammar-constrained decoding — the differentiation metric, proven on synthetic logits."""
from pathlib import Path

import numpy as np
import pytest

from serving.char_vocab import IDX, V, VOCAB, decode, encode
from serving.grammar_decoder import (ConstrainedDecoder, GrammarDFA,
                                     surface_forms)

GRAMMAR = Path(__file__).resolve().parent.parent / "configs" / "commands.yaml"


def _emissions_for(text: str, T_pad: int = 6) -> np.ndarray:
    """Synthetic log-probs strongly favoring `text` (blank between every char —
    exactly what a trained CTC net produces, incl. for repeated letters)."""
    ids = encode(text)
    seq = [0] * T_pad
    for i in ids:
        seq += [i, 0]
    seq += [0] * T_pad
    logp = np.full((len(seq), V), -20.0, np.float32)
    for t, i in enumerate(seq):
        logp[t, i] = 0.0
    return logp


def test_vocab_roundtrip():
    # no consecutive repeated chars: CTC greedy collapses repeats by design
    assert decode(encode("deploy solar panel")) == "deploy solar panel"
    assert decode(encode("channel")) == "chanel"   # 'nn' collapses — blanks needed (documented)
    assert encode("RT!") == [IDX["r"], IDX["t"]]          # unknown chars dropped


def test_constrained_matches_clean_emissions():
    dfa = GrammarDFA.from_grammar(GRAMMAR, max_channel=20)
    dec = ConstrainedDecoder(dfa)
    out = dec.decode(_emissions_for("read telemetry channel 5"))
    assert out["matched"] is True and out["text"] == "read telemetry channel 5"


def test_unconstrained_garble_is_rescued():
    """Emissions favor illegal 'red telemetry ...' -> grammar must find 'read ...'."""
    dfa = GrammarDFA.from_grammar(GRAMMAR, max_channel=20)
    dec = ConstrainedDecoder(dfa)
    logp = _emissions_for("red telemetry")
    # greedy on these emissions is NOT a legal command
    assert "red telemetry" not in surface_forms(GRAMMAR, max_channel=20)
    out = dec.decode(logp)
    assert "red telemetry" not in [out["text"]]         # vetoed
    assert out["matched"] and out["text"].startswith(("re",))  # nearest legal form


def test_off_grammar_speech_reports_unmatched():
    dfa = GrammarDFA.from_grammar(GRAMMAR, max_channel=20)
    dec = ConstrainedDecoder(dfa)
    out = dec.decode(_emissions_for("zzzz qqq"))
    assert out["matched"] is False                      # caller falls back gracefully


def test_lexicon_scale_is_sane():
    forms = surface_forms(GRAMMAR, max_channel=69)
    assert 20000 < len(forms) < 60000                   # big grammar, shared-prefix trie
    dfa = GrammarDFA(forms)
    assert dfa.size() < 400_000                         # RAM stays tiny
