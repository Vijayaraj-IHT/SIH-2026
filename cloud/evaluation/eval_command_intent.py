"""Command intent accuracy — the metric judges will quote (plan gate: >=97%).

Modes:
  offline:   --transcripts scored.jsonl   (rows: {text, hypothesis, reference_intent})
  full loop: --manifest test.jsonl --model base   (transcribe + route + score)

Comparison is field-wise against reference_intent from the corpus manifest:
action, subsystem, and any present slots (channel/mode/voltage). Exact match on
ALL fields = a correct command execution.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from serving.intent_router import IntentRouter  # noqa: E402

_FIELDS = ("action", "subsystem", "channel", "mode", "voltage")


def score_rows(rows, router: IntentRouter) -> dict:
    per_field = {f: {"ok": 0, "n": 0} for f in _FIELDS}
    exact = misses = 0
    fails = []
    for r in rows:
        ref = {k: v for k, v in (r.get("reference_intent") or {}).items() if v is not None}
        if not ref:
            continue
        hyp_text = r.get("hypothesis") if r.get("hypothesis") else r.get("text")
        intent = router.parse(hyp_text)
        hyp = intent if intent["type"] == "command" else {}
        ok = True
        for f, v in ref.items():
            per_field[f]["n"] += 1
            hv = hyp.get(f)
            if f == "channel":                     # corpora store "five", router yields 5
                from serving.intent_router import _ONES
                v_cmp = _ONES.get(str(v).lower(), v)
                match = (hv == v_cmp) or (str(hv) == str(v_cmp))
            elif f == "voltage":                   # "three point three" -> 3.3
                from serving.intent_router import normalize
                toks = normalize(str(v)).replace(" point ", ".").split()
                v_cmp = float(toks[0]) if toks else None
                match = (isinstance(hv, float) and v_cmp is not None and
                         abs(hv - v_cmp) < 1e-6)
            else:
                match = str(hv).lower() == str(v).lower() if hv is not None else False
            per_field[f]["ok"] += int(match)
            ok &= match
        exact += int(ok)
        misses += int(not ok)
        if not ok and len(fails) < 10:
            fails.append({"ref": ref, "route": intent, "heard": hyp_text})
    total = exact + misses
    return {"total": total, "exact_match": exact,
            "intent_accuracy": round(exact / total, 4) if total else 0.0,
            "per_field": {f: round(v["ok"] / v["n"], 4) if v["n"] else None
                          for f, v in per_field.items()},
            "sample_failures": fails}


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--transcripts", default=None)
    g.add_argument("--manifest", default=None)
    ap.add_argument("--model", default="base")
    ap.add_argument("--grammar", default=str(Path(__file__).parent.parent / "configs" / "commands.yaml"))
    ap.add_argument("--out", default=str(Path(__file__).parent.parent.parent / "experiments" / "asr"))
    a = ap.parse_args()

    router = IntentRouter(a.grammar)
    if a.transcripts:
        rows = [json.loads(l) for l in open(a.transcripts) if l.strip()]
        source = a.transcripts
    else:
        import numpy as np
        from faster_whisper import WhisperModel
        from evaluation.eval_snr_sweep import load_audio
        model = WhisperModel(a.model, device="auto", compute_type="auto")
        rows = []
        for r in [json.loads(l) for l in open(a.manifest) if l.strip()]:
            segs, _ = model.transcribe(load_audio(r["audio_path"]), language="en")
            rows.append({**r, "hypothesis": " ".join(s.text for s in segs)})
        source = f"{a.manifest} via {a.model}"

    res = score_rows(rows, router)
    rec = {"source": source, "ts": int(time.time()), **res}
    print(json.dumps(rec, indent=2))
    if a.out:
        out = Path(a.out)
        out.mkdir(parents=True, exist_ok=True)
        f = out / f"intent_eval_{int(time.time())}.json"
        f.write_text(json.dumps(rec, indent=2))
        print(f"saved -> {f}")


if __name__ == "__main__":
    main()
