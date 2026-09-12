# AGNI-ASR Training Runbook — Phase A (Session 2)

Verified commands. Target: first fine-tuned `agni-whisper-small-lora` +
published eval JSONs. GPU assumed: single RTX 4090/A10G/A100 (12 GB+ VRAM ok).

## 0. VM setup (5 min)

```bash
bash cloud/scripts/spot_vm_bootstrap.sh        # docker + repo + serving stack
cd SIH_MODEL/cloud
docker compose down                            # we need the GPU for training now
python -m venv .venv && source .venv/bin/activate
pip install torch                              # CUDA build (VM has drivers)
pip install -r requirements.txt -r requirements-train.txt
huggingface-cli login                          # for Common Voice + push-to-hub
```

## 1. Data spine (~1–2 h, mostly unattended)

```bash
cd data
bash fetch_corpora.sh                          # LS-100 + dev/test + MUSAN + SCv2 (~10 GB)
python build_command_corpus.py --max 3000 \
    --speakers aswin member2 member3 member4 member5 member6   # real names!
python build_command_corpus.py --max 3000 --synthesize piper \
    --voices en_US-lessac-medium en_GB-alan-medium             # after: pip install piper-tts
python make_manifests.py --max-librispeech 14200               # ~= 100 h Phase A
```

**Team task this week (offline, highest ROI):** record `recorder_sheet_*.md`
prompts (~20 min/person) → `cloud/recordings/<name>/AGNI_00001.wav`, and re-record
the 40 TEST-set utterances through the ESP32 (the ESMC set). Re-run `make_manifests.py`
afterward — it picks up audio automatically and always prefers ESP32 captures.

## 2. Phase-A LoRA fine-tune (~2–4 GPU-hours)

```bash
python training/train_whisper.py \
  --train data/manifests/train.jsonl --dev data/manifests/dev.jsonl \
  --model openai/whisper-small --lora \
  --augment --noise-dir data/raw/musan/noise/free-sound \
  --epochs 3 --batch 16 --grad-accum 8 --lr 1e-4 \
  --output runs/whisper_small_lora --push-to-hub <hf-user>/agni-whisper-small-lora
```

Watch: loss should fall from ~1.5 to <0.5; dev eval every 500 steps.
Spot safety: checkpoints land in `runs/.../checkpoint-500` — re-run with the same
`--output` to auto-resume. (Session 3 wires `--notifications` to W&B.)

## 3. Merge adapter → deploy to the gateway (10 min)

```bash
python - <<'PY'
from transformers import WhisperForConditionalGeneration
from peft import PeftModel
m = WhisperForConditionalGeneration.from_pretrained("openai/whisper-small")
m = PeftModel.from_pretrained(m, "runs/whisper_small_lora/adapter")
m = m.merge_and_unload()
m.save_pretrained("runs/agni-whisper-small-v1")
PY
python -c "from faster_whisper import WhisperModel; WhisperModel('runs/agni-whisper-small-v1', device='cuda')"
# CTranslate2 converter (one-time): pip install ctranslate2
ct2-transformers-converter --model runs/agni-whisper-small-v1 \
  --output_dir runs/agni-whisper-small-v1-ct2 --quantization int8
AGNI_MODEL_SIZE=/opt/SIH_MODEL/cloud/runs/agni-whisper-small-v1-ct2 docker compose up -d
```

## 4. Publish the acceptance numbers

```bash
python evaluation/eval_snr_sweep.py --manifest data/manifests/test.jsonl \
  --model runs/agni-whisper-small-v1-ct2 --snr clean,20,10,0 \
  --noise-dir data/raw/musan/noise/free-sound --out ../experiments/asr
python evaluation/eval_command_intent.py --manifest data/manifests/test.jsonl \
  --model runs/agni-whisper-small-v1-ct2
```

Targets (plan §7): ESMC-quiet WER ≤ 5 % · SNR10 ≤ 12 % · grammar intent ≥ 97 %.
Files land in `experiments/asr/eval_*.json` next to your existing baseline JSONs —
attach them to the SIH report.

## Kill criteria & cost guardrails

| Condition | Action |
|---|---|
| dev WER plateaus 3 evals | stop run, audit data mix first (don't just train longer) |
| GPU spend > ₹6,000 | freeze Phase A, ship numbers, Phase B only after judging slot confirmed |
| command intent < 90 % | corpus gap, not model gap: check `sample_failures` in intent JSON, add templates |

## Session 3 addendum — the command model (Model A)

```bash
# 1. Train the CTC command model (~1-2 GPU-hours on the command corpus mix)
python training/train_ctc_command_model.py \
  --train data/manifests/train.jsonl --filter-corpus agni_commands,librispeech \
  --augment --noise-dir data/raw/musan/noise/free-sound \
  --epochs 15 --batch 16 --lr 3e-4 --output runs/conformer_ctc

# 2. Enable the fast path in the gateway
#    cloud.yaml -> command_model.enabled: true, ckpt_path: ../runs/conformer_ctc/conformer_ctc.pt
#    (or: AGNI-style env swap; restart gateway) — WS clients now get REAL partials.

# 3. Verify the grammar metric (the judge headline)
python evaluation/eval_command_intent.py --manifest data/manifests/test.jsonl --model runs/agni-whisper-small-v1-ct2
```

Grammar-constrained decoding is ON by default (`grammar_decode: true`) —
greedy fallback is automatic for off-grammar speech (`engine: ctc-greedy`).
Alternative industrial backbone (only if needed, true token streaming): NeMo
FastConformer — `python training/train_conformer_nemo.py` emits config + runbook;
expect extra setup time vs the single-pip torchaudio route.
