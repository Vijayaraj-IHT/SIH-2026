"""OPTIONAL alternative backbone: NVIDIA NeMo FastConformer (VM-only path).

Why this exists: torchaudio's conformer-CTC (train_conformer_ctc.py) is the
recommended hackathon route — 1 pip install, no dependency hell. But if the team
needs true token-level streaming or an RNN-T head later, NeMo's
FastConformer-RNNT is the industry-grade option. This script EMITS the NeMo
config + the exact commands; it purposely does not manage the NeMo install
(`pip install nemo_toolkit[asr]` on a CUDA VM with matching torch).

Usage:  python train_conformer_nemo.py --out nemo_cfg/ && cat nemo_cfg/RUNME.md
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

CONFIG = """
# FastConformer-CTC ~120M, char vocab — matches AGNI plan Model A
name: "agni-fast-conformer-ctc"
model:
  sample_rate: 16000
  train_ds:
    manifest_filepath: "data/manifests/train.jsonl"      # nemo-style manifests
    batch_size: 16
  preprocessing: {n_mels: 80, n_fft: 512, window_size: 0.025, window_stride: 0.01}
  encoder:
    _target_: nemo.collections.asr.modules.ConformerEncoder
    feat_in: 80
    n_layers: 17
    d_model: 512
    subsampling: dw_striding          # 8x downsampling = the 'fast' in FastConformer
    subsampling_factor: 8
    conv_kernel_size: 9
    ff_expansion_factor: 4
    self_attention_model: rel_pos
    n_heads: 8
    dropout: 0.1
    dropout_att: 0.1
  decoder:
    _target_: nemo.collections.asr.modules.ConvASRDecoder
    feat_in: 512
    num_classes: 39                   # == serving/char_vocab.V (blank + 38)
trainer:
  max_epochs: 20
  accelerator: gpu
  precision: bf16
"""

RUNME = """# NeMo FastConformer path (VM only)
pip install "nemo_toolkit[asr]" Cython
python - <<'PY'
# convert our manifests to NeMo manifest schema (audio_filepath/duration/text)
import json, soundfile as sf, sys
for split in ("train", "dev"):
    with open(f"data/manifests/{split}.jsonl") as f, open(f"data/manifests/{split}_nemo.json", "w") as g:
        for l in f:
            r = json.loads(l)
            if not r["audio_path"]:
                continue
            d = sf.info(r["audio_path"])
            g.write(json.dumps({"audio_filepath": r["audio_path"],
                                "duration": d.frames / d.samplerate,
                                "text": r["text"]}) + "\\n")
PY
python ${NEMO_HOME}/examples/asr/asr_ctc/speech_to_text_ctc.py \\
    --config-path nemo_cfg --config-name agni_fastconformer.yaml
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="nemo_cfg")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "agni_fastconformer.yaml").write_text(CONFIG)
    (out / "RUNME.md").write_text(RUNME)
    print(json.dumps({"wrote": [str(out / "agni_fastconformer.yaml"),
                                str(out / "RUNME.md")]}, indent=2))


if __name__ == "__main__":
    main()
