"""Expand the command grammar into the AGNI command corpus (plan §5 step 1-2).

Sources of speech per utterance (mix by design):
  A) TTS (Piper, MIT)  — bulk coverage; run `--synthesize piper` on the VM
  B) Team recordings   — drop wavs into recordings/<speaker>/<utterance_id>.wav
  C) ESMC              — same files re-captured through the ESP32 INMP441 path

Outputs:
  <out>/metadata.csv                 utterance_id,text,action,subsystem,split,status
  <out>/manifest.jsonl               training-manifest rows (audio_path filled later)
  <out>/recorder_sheet_<speaker>.md  exact prompt list for each human speaker
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import shutil
import subprocess
from pathlib import Path

import yaml

_NUM_WORDS = ["one", "two", "three", "four", "five", "six", "seven", "eight"]
_VOLTAGES = ["three point three", "five point zero", "twelve point zero"]


def expand_corpus(grammar: dict, max_utts: int = 3000, seed: int = 42) -> list[dict]:
    rng = random.Random(seed)
    verbs = grammar["verbs"]
    subsystems = grammar["subsystems"]
    modes = grammar["modes"]
    keywords = grammar.get("enrolled_keywords", [])

    rows: list[dict] = []

    def add(text, action, subsystem, **extra):
        rows.append({"text": text, "action": action, "subsystem": subsystem, **extra})

    for verb_canon, aliases in verbs.items():
        spoken = list(dict.fromkeys([verb_canon] + aliases[:2]))   # dedupe e.g. [arm]+[arm]
        for sub_canon, sub_aliases in subsystems.items():
            for v_alias in spoken:
                s_alias = sub_aliases[0]
                base = f"{v_alias} {s_alias}"
                if verb_canon in ("read",):
                    for n in _NUM_WORDS[:4]:
                        add(f"{base} channel {n}", "read", sub_canon, channel=n)
                if verb_canon in ("switch",):
                    for mode in modes:
                        add(f"{v_alias} {s_alias} to {mode} mode", "switch",
                            sub_canon, mode=mode)
                elif verb_canon in ("set",):
                    for v in _VOLTAGES:
                        add(f"{v_alias} {s_alias} voltage to {v}", "set", sub_canon, voltage=v)
                else:
                    add(base, verb_canon, sub_canon)
                    if verb_canon == "read":
                        continue

    # wake-keyword-prefixed variants (operator habit: "AGNI, read telemetry channel five")
    for r in list(rng.sample(rows, min(len(rows), 400))):
        rows.append({**r, "text": f"{rng.choice(keywords) if keywords else ''} {r['text']}".strip()})

    # defensive global dedupe on spoken text (aliases may converge)
    seen: set = set()
    rows = [r for r in rows if not (r["text"] in seen or seen.add(r["text"]))]

    rng.shuffle(rows)
    rows = rows[:max_utts]
    for i, r in enumerate(rows):
        r["id"] = f"AGNI_{i + 1:05d}"
    rng.shuffle(rows)
    n = len(rows)
    for i, r in enumerate(rows):
        r["split"] = "train" if i < 0.90 * n else ("dev" if i < 0.95 * n else "test")
    return rows


def reference_intent(row: dict) -> dict:
    out = {"action": row.get("action"), "subsystem": row.get("subsystem")}
    for k in ("channel", "mode", "voltage"):
        if row.get(k):
            out[k] = row[k]
    return out


def write_outputs(rows: list[dict], out_dir: Path, speakers: list[str]):
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "metadata.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["id", "text", "action", "subsystem", "split", "status"])
        w.writeheader()
        for r in rows:
            w.writerow({"id": r["id"], "text": r["text"], "action": r.get("action"),
                        "subsystem": r.get("subsystem"), "split": r["split"],
                        "status": "pending"})  # pending -> tts / recorded / esmc
    with open(out_dir / "manifest.jsonl", "w") as f:
        for r in rows:
            f.write(json.dumps({"id": r["id"], "audio_path": "", "text": r["text"],
                                "corpus": "agni_commands", "split": r["split"],
                                "reference_intent": reference_intent(r)}) + "\n")
    # recorder sheets: round-robin real-speech coverage, dev/test 100% human
    for si, sp in enumerate(speakers):
        lines = [f"# Recorder sheet — {sp}",
                 "Read each line once, naturally, then a second time **urgently**.",
                 "Save as: recordings/{}/<ID>.wav  (16 kHz mono, any phone/laptop mic)\n"
                 .format(sp)]
        for i, r in enumerate(rows):
            if i % len(speakers) == si or r["split"] != "train":
                lines.append(f"- [ ] `{r['id']}` — “{r['text']}”")
        (out_dir / f"recorder_sheet_{sp}.md").write_text("\n".join(lines))


def synthesize_piper(out_dir: Path, rows: list[dict], voices: list[str]):
    if not shutil.which("piper"):
        raise SystemExit("piper not found — `pip install piper-tts==1.2.0` on the VM")
    wavs = out_dir / "wav"
    wavs.mkdir(exist_ok=True)
    for i, r in enumerate(rows):
        voice = voices[i % len(voices)]
        out = wavs / f"{r['id']}.wav"
        if out.exists():
            continue
        subprocess.run(["piper", "--model", voice, "--output_file", str(out)],
                       input=r["text"].encode(), check=True)
    print(f"synthesized -> {wavs}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--grammar", default=str(Path(__file__).parent.parent / "configs" / "commands.yaml"))
    ap.add_argument("--out", default=str(Path(__file__).parent / "out" / "commands"))
    ap.add_argument("--max", type=int, default=3000)
    ap.add_argument("--speakers", nargs="*", default=["member1", "member2", "member3",
                                                      "member4", "member5", "member6"])
    ap.add_argument("--synthesize", choices=["piper"], default=None)
    ap.add_argument("--voices", nargs="*", default=["en_US-lessac-medium", "en_GB-alan-medium"])
    a = ap.parse_args()
    grammar = yaml.safe_load(open(a.grammar))
    rows = expand_corpus(grammar, max_utts=a.max)
    out = Path(a.out)
    write_outputs(rows, out, a.speakers)
    splits = {}
    for r in rows:
        splits[r["split"]] = splits.get(r["split"], 0) + 1
    print(f"expanded {len(rows)} utterances -> {out} | splits: {splits}")
    if a.synthesize:
        synthesize_piper(out, rows, a.voices)


if __name__ == "__main__":
    main()
