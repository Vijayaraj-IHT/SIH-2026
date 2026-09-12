"""WER/CER per SNR bucket — the eval harness from plan §7.

  python eval_snr_sweep.py --manifest eval.jsonl --model base --snr clean,10,0 \
      --noise-dir ../data/raw/musan/noise/free-sound --out ../../experiments/asr/

Writes experiments-style JSON: one entry per (model, snr) with wer/cer/latency.
Noise fallback: seeded white noise scaled the same way (works before MUSAN is
downloaded, documented in the JSON as 'white').
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from data.channel_augment import add_noise, load_noise_pool  # noqa: E402


def load_audio(path: str, sr_target: int = 16000) -> np.ndarray:
    import soundfile as sf
    x, sr = sf.read(path, dtype="float32", always_2d=True)
    x = x.mean(axis=1)
    if sr != sr_target:
        n = int(x.size * sr_target / sr)
        x = np.interp(np.linspace(0, x.size - 1, n), np.arange(x.size), x)
    return x.astype(np.float32)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--model", default="base")
    ap.add_argument("--snr", default="clean,20,10,0")
    ap.add_argument("--noise-dir", default=None)
    ap.add_argument("--max", type=int, default=200)
    ap.add_argument("--out", default=str(Path(__file__).parent.parent.parent / "experiments" / "asr"))
    ap.add_argument("--language", default="en")
    a = ap.parse_args()

    from faster_whisper import WhisperModel
    from jiwer import cer, wer
    import jiwer.transforms as tr

    # canonical ASR-paper normalization: case/punctuation differences must NOT count
    _norm = tr.Compose([tr.ToLowerCase(), tr.RemovePunctuation(),
                        tr.RemoveMultipleSpaces(), tr.Strip()])
    norm_words = tr.Compose([_norm, tr.ReduceToListOfListOfWords()])
    norm_chars = tr.Compose([_norm, tr.ReduceToListOfListOfChars()])
    rows = [json.loads(l) for l in open(a.manifest) if l.strip()][: a.max]
    rng = np.random.default_rng(42)
    noise_pool = load_noise_pool(a.noise_dir) if a.noise_dir else []
    model = WhisperModel(a.model, device="auto", compute_type="auto")
    results = {}
    t_start = time.perf_counter()

    for snr in [s.strip() for s in a.snr.split(",")]:
        refs, hyps, lat, clean_refs = [], [], 0, 0
        for r in rows:
            ref = (r.get("text") or "").strip()
            if not ref:
                continue
            x = load_audio(r["audio_path"])
            if snr.lower() != "clean":
                if noise_pool:
                    x = add_noise(x, noise_pool[int(rng.integers(len(noise_pool)))],
                                  float(snr), rng)
                else:
                    x = add_noise(x, rng.standard_normal(x.size).astype(np.float32),
                                  float(snr), rng)
            t0 = time.perf_counter()
            segs, _info = model.transcribe(x, language=a.language, beam_size=1)
            lat += time.perf_counter() - t0
            refs.append(ref)
            hyps.append(" ".join(s.text for s in segs))
            clean_refs += 1
        key = "clean" if snr.lower() == "clean" else f"snr{snr}db"
        tag = "musan" if noise_pool else "white"
        results[key] = {"n": clean_refs,
                        "wer": round(wer(refs, hyps, reference_transform=norm_words,
                                         hypothesis_transform=norm_words), 4),
                        "cer": round(cer(refs, hyps, reference_transform=norm_chars,
                                         hypothesis_transform=norm_chars), 4),
                        "avg_latency_s": round(lat / max(clean_refs, 1), 3),
                        "noise_source": tag if key != "clean" else None}
        print(f"{key:>10}  WER {results[key]['wer']:.3f}  CER {results[key]['cer']:.3f} "
              f"({clean_refs} files, {tag if key != 'clean' else '-'})")

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rec = {"model": a.model, "manifest": a.manifest,
           "wall_seconds": round(time.perf_counter() - t_start, 1), "results": results}
    fname = out / f"eval_{a.model.replace('/', '_')}_{int(time.time())}.json"
    fname.write_text(json.dumps(rec, indent=2))
    print(f"\nsaved -> {fname}")


if __name__ == "__main__":
    main()
