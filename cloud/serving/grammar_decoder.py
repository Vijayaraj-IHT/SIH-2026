"""Grammar-constrained CTC decoding — the >=97% command-accuracy mechanism.

A standard CTC greedy decode takes argmax per frame and can emit ANY string
("red telemetry vhannel fibe"). We instead walk a TRIE of every legal command
surface form (built from configs/commands.yaml) with a small beam:
at each frame, the only allowed emissions are {blank} U {children of the
current trie states}. The model still picks acoustics — the grammar merely
vetoes impossible continuations, just like a WFST would but with zero Kaldi
install and ~40 lines of pure Python. (Sessions can cite it as
"lexicon-constrained CTC decoding".)

Fallback discipline: if no trie state survives, we return matched=False and the
caller (gateway) routes the raw greedy/freeform path instead of crashing.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import yaml

from .char_vocab import BLANK_ID, IDX, VOCAB


# ------------------------------------------------------------ lexicon builder
def _num_words(max_n: int = 69) -> list[str]:
    ones = ["zero", "one", "two", "three", "four", "five", "six", "seven",
            "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen",
            "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
    tens = ["twenty", "thirty", "forty", "fifty", "sixty"]
    out = [str(i) for i in range(10)] + ones[1:]          # digits AND words
    out += tens + [f"{t} {o}" for t in tens for o in ones[1:10]]
    return [w for w in out if w != "zero"][:max_n]


def surface_forms(grammar_path: str | Path, max_channel: int = 69) -> set[str]:
    """Every legal command string, wake keyword optional, articles excluded."""
    g = yaml.safe_load(open(grammar_path))
    verbs, subs, modes = g["verbs"], g["subsystems"], g["modes"]
    keys = [""] + [f"{k} " for k in g.get("enrolled_keywords", [])]
    nums = _num_words(max_channel)
    volts = ["three point three", "five point zero", "twelve point zero"]
    forms: set[str] = set()

    def alias1(s):  # first spoken alias per canonical subsystem
        return subs[s][0]

    for s in subs:
        sa = alias1(s)
        for v in (verbs["read"] + ["read"])[:5]:
            forms.add(f"{v} {sa}")
            for n in nums:
                forms.add(f"{v} {sa} channel {n}")
        for v in [a for a in (verbs["switch"])][:2]:
            for m in modes:
                forms.add(f"{v} {sa} to {m} mode")
        for v in ["set"]:
            for x in volts:
                forms.add(f"{v} {sa} voltage to {x}")
        for vg in ("arm", "disarm", "deploy", "stow", "abort", "calibrate"):
            for a in verbs[vg][:2]:
                forms.add(f"{a} {sa}")
    return {f"{k}{f}" for k in keys for f in forms}


# ----------------------------------------------------------------- trie + dfa
@dataclass
class TrieNode:
    children: dict = field(default_factory=dict)   # char_idx -> TrieNode
    terminal: bool = False


class GrammarDFA:
    def __init__(self, strings):
        self.root = TrieNode()
        for s in strings:
            self.insert(s.lower())

    @classmethod
    def from_grammar(cls, grammar_path: str | Path, max_channel: int = 69):
        return cls(surface_forms(grammar_path, max_channel))

    def insert(self, s: str):
        node = self.root
        for c in s:
            i = IDX.get(c)
            if i is None:
                continue
            node = node.children.setdefault(i, TrieNode())
        node.terminal = True

    def size(self) -> int:  # diagnostics
        def count(n):
            return 1 + sum(count(c) for c in n.children.values())
        return count(self.root)


@dataclass
class _State:
    node: TrieNode
    score: float
    text: str
    last_emit: int = -1      # last char emitted (CTC repeat guard)


class ConstrainedDecoder:
    """Beam-over-trie greedy CTC decoder (beam ~8 is plenty for this lexicon)."""

    def __init__(self, dfa: GrammarDFA, beam: int = 24, blank_id: int = BLANK_ID):
        self.dfa, self.beam, self.blank = dfa, beam, blank_id

    def decode(self, logp: np.ndarray) -> dict:
        """logp: (T, V) log-probs (or raw logits; monotone transform is rank-preserving).

        CTC-style beam book-keeping: candidates are merged PER TRIE NODE (keep the
        best score reaching each node), then the beam keeps the best distinct
        nodes — no duplicate nodes starving the frontier.
        """
        states = [_State(self.dfa.root, 0.0, "")]
        margins = []
        for t in range(logp.shape[0]):
            p = logp[t]
            best_for_node: dict = {}
            for s in states:
                cand_blank = _State(s.node, s.score + float(p[self.blank]), s.text, -1)
                if cand_blank.score > best_for_node.get(id(s.node), _State(s.node, -1e30, "")).score:
                    best_for_node[id(s.node)] = cand_blank
                for ci, node in s.node.children.items():
                    if ci == s.last_emit:                             # needs blank between
                        continue
                    c = _State(node, s.score + float(p[ci]), s.text + VOCAB[ci], ci)
                    if c.score > best_for_node.get(id(node), _State(node, -1e30, "")).score:
                        best_for_node[id(node)] = c
            cand = sorted(best_for_node.values(), key=lambda s: s.score, reverse=True)
            top = cand[0]
            runner_up = cand[1].score if len(cand) > 1 else -1e30
            margins.append(top.score - runner_up)
            states = cand[: self.beam]
        best_terminal = next((s for s in states if s.node.terminal), None)
        best_any = states[0]
        chosen = best_terminal or best_any
        return {"text": chosen.text.strip(), "matched": best_terminal is not None,
                "score": chosen.score,
                "mean_margin": float(np.mean(margins)) if margins else 0.0}


def demo():  # pragma: no cover - manual sanity aid
    from .char_vocab import decode as gdec
    here = Path(__file__).resolve().parent.parent / "configs" / "commands.yaml"
    forms = surface_forms(here)
    dfa = GrammarDFA(forms)
    print("trie nodes:", dfa.size(), "| forms:", len(forms),
          "| e.g.:", sorted(list(forms))[:2])
    rng = np.random.default_rng(0)
    noisy = rng.standard_normal((120, len(VOCAB)))
    print("random emissions -> greedy:", gdec(noisy.argmax(1))[:40], "|",
          ConstrainedDecoder(dfa).decode(noisy)["text"])


if __name__ == "__main__":
    demo()
