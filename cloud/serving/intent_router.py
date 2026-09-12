"""Grammar-based intent router — transcripts -> structured command JSON.

Session-1 parser: regex/slot filling over commands.yaml (deterministic,
auditable, zero model cost). Session-3 upgrade path: WFST shallow fusion during
Model-A decode; freeform utterances fall back here unchanged.

Contract (consumed by ESP32 firmware / dashboard):
  {"type": "command", "action": "read", "subsystem": "telemetry", "channel": 5,
   "raw": "read telemetry channel five"}
  {"type": "freeform", "raw": "what is the battery voltage trend"}
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

_ONES = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
    "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
}
_TENS = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
         "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90}
# Longest-first ordering matters: "eighty" vs "eight" (prefix) — otherwise
# "eighty three" parses as "three". Non-capturing scope makes the optional
# ONES suffix apply to ANY number word, not just the last alternative.
_ALT = "|".join(sorted(list(_ONES) + list(_TENS), key=len, reverse=True))
_ONES_ALT = "|".join(sorted(_ONES, key=len, reverse=True))
_NUMWORD = re.compile(rf"\b((?:{_ALT})(?: (?:{_ONES_ALT}))?)\b")


def _numsub(m: re.Match) -> str:
    parts = m.group(0).split()
    val = _TENS[parts[0]] + _ONES[parts[1]] if len(parts) == 2 else _ONES[parts[0]]
    return str(val)


def normalize(text: str) -> str:
    """lowercase, strip punctuation, number-words -> digits, collapse spaces."""
    t = text.lower()
    t = re.sub(r"[^\w\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    t = _NUMWORD.sub(_numsub, t)
    return t


class IntentRouter:
    def __init__(self, grammar_path: str | Path, freeform_fallback: bool = True):
        with open(grammar_path, "r", encoding="utf-8") as f:
            g = yaml.safe_load(f)
        self.freeform_fallback = freeform_fallback
        self.keywords = set(g.get("enrolled_keywords", []))
        self.modes = set(g.get("modes", []))

        # alias -> canonical (verbs & subsystems), longest alias first so
        # "solar panel" wins over "panels"
        self.verb_map = {a: k for k, als in g["verbs"].items() for a in als} | \
                        {k: k for k in g["verbs"]}
        self.sub_map = {a: k for k, als in g["subsystems"].items() for a in als} | \
                       {k.replace("_", " "): k for k in g["subsystems"]}
        self._sub_pattern = "|".join(sorted(map(re.escape, self.sub_map), key=len, reverse=True))

    # ------------------------------------------------------------------ parse
    def parse(self, raw_text: str) -> dict:
        t = normalize(raw_text)

        # strip spoken wake-word / politeness / articles
        first = t.split(" ", 1)[0] if t else ""
        if first in self.keywords:
            t = t.split(" ", 1)[1] if " " in t else ""
        for word in ("please", "the", "a", "an"):
            t = re.sub(rf"\b{word}\b", "", t)
        t = re.sub(r"\s+", " ", t).strip()
        if not t:
            return self._fallback(raw_text, reason="empty_after_strip")

        verb = None
        head = t.split(" ", 1)[0]
        if head in self.verb_map:
            verb = self.verb_map[head]
            rest = t.split(" ", 1)[1] if " " in t else ""

        m = re.search(self._sub_pattern, t)
        subsystem = self.sub_map[m.group(0)] if m else None

        intent = {"type": "command", "action": verb, "subsystem": subsystem, "raw": raw_text}

        if verb == "switch":
            m2 = re.search(r"\bto (" + "|".join(map(re.escape, self.modes)) + r")", t)
            if not m2 or subsystem is None:
                return self._fallback(raw_text, reason="switch_needs_subsystem+mode")
            intent.update(action="switch", mode=m2.group(1))
            return intent

        if verb == "set" and subsystem:
            m3 = re.search(r"(\d+)\s+point\s+(\d+)", t)
            if m3:
                intent["voltage"] = float(f"{m3.group(1)}.{m3.group(2)}")
                return intent
            return self._fallback(raw_text, reason="set_needs_voltage")

        m4 = re.search(r"\bchannel (\d+)\b", t)
        if m4:
            intent["channel"] = int(m4.group(1))

        if verb is None or subsystem is None:
            return self._fallback(raw_text, reason="missing_verb_or_subsystem")
        return intent

    def _fallback(self, raw: str, reason: str) -> dict:
        if self.freeform_fallback:
            return {"type": "freeform", "raw": raw, "note": reason}
        return {"type": "unknown", "raw": raw, "error": reason}


if __name__ == "__main__":
    here = Path(__file__).resolve().parent.parent / "configs" / "commands.yaml"
    r = IntentRouter(here)
    for s in ["agni read telemetry channel five", "vayu deploy the solar panel",
              "jump abort payload", "cable switch transponder to silent mode",
              "set heater voltage to three point three",
              "what is the battery temperature trend"]:
        import json
        print(json.dumps(r.parse(s)))
