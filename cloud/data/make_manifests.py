"""Unified training/eval manifests: every corpus -> one JSONL schema.

  {"audio_path": ..., "text": ..., "corpus": ..., "split": ...,
   "speaker": ..., "duration_s": ..., "reference_intent": {...} | null}

Usage
-----
  python make_manifests.py --raw raw --out manifests --recordings ../recordings
Scans LibriSpeech / Speech Commands / Common Voice / AGNI command corpus and
emits train.jsonl, dev.jsonl, test.jsonl + stats.json (repo experiments style).
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import re
from pathlib import Path


def write_jsonl(rows, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def load_jsonl(path: str | Path) -> list[dict]:
    with open(path) as f:
        return [json.loads(l) for l in f if l.strip()]


def norm_text(t: str) -> str:
    """Transcript hygiene per plan: lowercase, strip punctuation, collapse space."""
    t = t.lower()
    t = re.sub(r"[^\w\s']", " ", t)
    return re.sub(r"\s+", " ", t).strip()


# ------------------------------------------------------------- corpus scanners
def scan_librispeech(root: Path, max_per_subset: int | None = None) -> list[dict]:
    rows = []
    for subset_root in sorted(root.glob("LibriSpeech/*")):
        split = {"dev-clean": "dev", "test-clean": "test"}.get(subset_root.name, "train")
        for trans in subset_root.rglob("*.trans.txt"):
            text_map = dict(l.split(" ", 1) for l in trans.read_text().splitlines())
            for utt_id, text in text_map.items():
                audio = trans.parent / f"{utt_id}.flac"
                if audio.exists():
                    rows.append({"audio_path": str(audio), "text": norm_text(text),
                                 "corpus": "librispeech", "split": split,
                                 "speaker": utt_id.split("-")[0],
                                 "reference_intent": None})
                    if max_per_subset and split == "train" and \
                            len([r for r in rows if r["split"] == "train"]) >= max_per_subset:
                        return rows
    return rows


def scan_speech_commands(root: Path, max_rows: int = 5000, seed: int = 42) -> list[dict]:
    sc = root / "speech_commands"
    rows = []
    for wav in sorted(sc.glob("*/*.wav")):
        label = wav.parent.name
        if label.startswith("_"):
            continue
        rows.append({"audio_path": str(wav), "text": label, "corpus": "speech_commands",
                     "split": "train", "speaker": wav.stem.split("_nohash_")[0],
                     "reference_intent": None})
    random.Random(seed).shuffle(rows)
    return rows[:max_rows]


def scan_common_voice(root: Path) -> list[dict]:
    """Pairs fetch_corpora.sh wav dump with transcripts (cv_NNNNNN.wav)."""
    cv = root / "common_voice_en"
    if not cv.exists():
        return []
    try:
        from datasets import load_dataset
        ds = load_dataset("mozilla-foundation/common_voice_17_0", "en",
                          split="validated", trust_remote_code=True)
        sentences = [norm_text(s) for s in ds["sentence"]]
    except Exception as e:
        print(f"[warn] CV transcripts unavailable ({e}); skipping")
        return []
    rows = []
    for wav in sorted(cv.glob("cv_*.wav")):
        i = int(wav.stem.split("_")[1])
        if i < len(sentences):
            rows.append({"audio_path": str(wav), "text": sentences[i],
                         "corpus": "common_voice", "split": "train",
                         "speaker": "cv", "reference_intent": None})
    return rows


def scan_command_corpus(meta_csv: Path, recordings_dirs: list[Path]) -> list[dict]:
    """metadata.csv rows + whichever audio exists (wav/ -- TTS, recordings/<sp>/,
    esmc/ -- priority: esmc > recordings > tts)."""
    if not meta_csv.exists():
        return []
    rows = []
    with open(meta_csv) as f:
        for m in csv.DictReader(f):
            audio = ""
            for base in recordings_dirs:
                for cand in base.rglob(f"{m['id']}.wav"):
                    audio = str(cand)
                    if "esmc" in cand.parts:
                        break
                if audio:
                    break
            tts = meta_csv.parent / "wav" / f"{m['id']}.wav"
            if not audio and tts.exists():
                audio = str(tts)
            rows.append({"audio_path": audio, "text": norm_text(m["text"]),
                         "corpus": "agni_commands", "split": m["split"],
                         "speaker": Path(audio).parent.name if audio else "tts",
                         "reference_intent": {"action": m["action"], "subsystem": m["subsystem"]},
                         "status": "ready" if audio else "pending"})
    return rows


def stats(rows: list[dict]) -> dict:
    import soundfile as sf
    per: dict = {}
    for r in rows:
        if not r["audio_path"]:
            continue
        try:
            info = sf.info(r["audio_path"])
            dur = info.frames / info.samplerate
        except Exception:
            continue
        key = f'{r["corpus"]}/{r["split"]}'
        per.setdefault(key, {"files": 0, "hours": 0.0})
        per[key]["files"] += 1
        per[key]["hours"] = round(per[key]["hours"] + dur / 3600, 3)
    return {"total_rows": len(rows), "with_audio": sum(v["files"] for v in per.values()),
            "by_corpus_split": per}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default=str(Path(__file__).parent / "raw"))
    ap.add_argument("--commands", default=str(Path(__file__).parent / "out" / "commands"))
    ap.add_argument("--out", default=str(Path(__file__).parent / "manifests"))
    ap.add_argument("--recordings", nargs="*", default=[str(Path(__file__).parent.parent / "recordings")])
    ap.add_argument("--max-librispeech", type=int, default=None,
                    help="cap train rows for Phase A (e.g. 14200 ~= 100 h)")
    a = ap.parse_args()
    raw, out = Path(a.raw), Path(a.out)

    rows = scan_librispeech(raw, a.max_librispeech)
    rows += scan_speech_commands(raw)
    rows += scan_common_voice(raw)
    rows += scan_command_corpus(Path(a.commands) / "metadata.csv",
                                [Path(d) for d in a.recordings])

    ready = [r for r in rows if r["audio_path"]]
    pending = [r for r in rows if not r["audio_path"]]
    for split in ("train", "dev", "test"):
        write_jsonl([r for r in ready if r["split"] == split], out / f"{split}.jsonl")
    write_jsonl(pending, out / "pending.jsonl")
    s = stats(ready)
    (out / "stats.json").write_text(json.dumps(s, indent=2))
    print(json.dumps(s, indent=2))
    print(f"\nmanifests -> {out}  ({len(pending)} utterances pending audio)")


if __name__ == "__main__":
    main()
