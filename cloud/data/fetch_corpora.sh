#!/usr/bin/env bash
# ==============================================================================
# AGNI-ASR corpus fetcher — downloads into cloud/data/raw/
#   bash fetch_corpora.sh          # compact Phase-A set (~10 GB)
#   bash fetch_corpora.sh full     # adds LibriSpeech train-360 (~26 GB more)
# Phase A (150 h) is designed to fit a Kaggle/vast.ai notebook disk.
# Common Voice requires a (free) signed-in HF account:  huggingface-cli login
# ==============================================================================
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/raw"
mkdir -p "$ROOT"
cd "$ROOT"

fetch () {  # fetch <url> <out.tar.gz>
  if [ -f "$2" ]; then echo "[skip] $2 exists"; else
    echo "[get ] $2"; curl -fL --retry 3 -C - -o "$2" "$1"; fi
}

echo "== LibriSpeech (CC BY 4.0) =="
fetch http://www.openslr.org/resources/12/train-clean-100.tar.gz train-clean-100.tar.gz
fetch http://www.openslr.org/resources/12/dev-clean.tar.gz       dev-clean.tar.gz
fetch http://www.openslr.org/resources/12/test-clean.tar.gz      test-clean.tar.gz
for z in train-clean-100 dev-clean test-clean; do
  [ -d "LibriSpeech/$z" ] || { echo "[untar] $z"; tar -xzf "$z.tar.gz"; }
done

if [[ "${1:-}" == "full" ]]; then
  fetch http://www.openslr.org/resources/12/train-clean-360.tar.gz train-clean-360.tar.gz
  [ -d "LibriSpeech/train-clean-360" ] || tar -xzf train-clean-360.tar.gz
fi

echo "== MUSAN noise corpus (ODC-BY) =="
fetch http://www.openslr.org/resources/17/musan.tar.gz musan.tar.gz
[ -d musan ] || tar -xzf musan.tar.gz

echo "== Google Speech Commands v2 (CC BY 4.0) — also used by the edge encoder =="
fetch http://download.tensorflow.org/data/speech_commands_v0.02.tar.gz scv2.tar.gz
mkdir -p speech_commands
[ -f speech_commands/yes/004ae714_nohash_0.wav ] 2>/dev/null || tar -xzf scv2.tar.gz -C speech_commands

echo "== Mozilla Common Voice 17 en (CC-0) — needs HF auth =="
if huggingface-cli whoami >/dev/null 2>&1; then
  python - <<'PY'
from datasets import load_dataset
import soundfile as sf, pathlib
out = pathlib.Path("common_voice_en"); out.mkdir(exist_ok=True)
ds = load_dataset("mozilla-foundation/common_voice_17_0", "en",
                  split="validated", trust_remote_code=True)
for i, r in enumerate(ds.select(range(min(30000, len(ds))))):
    sf.write(out / f"cv_{i:06d}.wav", r["audio"]["array"], r["audio"]["sampling_rate"])
print("CV files:", len(list(out.glob('*.wav'))))
PY
  echo "[note] transcripts re-joined by make_manifests.py --common-voice"
else
  echo "[warn] not logged into HF — skipping Common Voice (huggingface-cli login)"
fi

echo "=============================================================="
echo " Done. Next:  python make_manifests.py --config ../configs/cloud.yaml"
echo " Disk used:"; du -sh "$ROOT"
echo "=============================================================="
