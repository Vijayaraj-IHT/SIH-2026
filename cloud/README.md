# AGNI-ASR — SIH-26172 Cloud Speech Layer

Cloud/ground-station ASR that receives the ESP32 voice-activator handover,
transcribes, **co-verifies the wake word server-side**, and returns structured
command intents. Session 1 delivers the full zero-training pipeline:
`faster-whisper` (zero-shot) → grammar intent router → MQTT/REST.
Fine-tuned models (the actual cloud *training*) plug in from Session 2 onward
with **zero gateway changes**.

## Layout

```
cloud/
├── configs/        cloud.yaml (service) · commands.yaml (grammar = corpus + WFST source of truth)
├── serving/        api_gateway · pipeline · asr_worker · co_verifier · intent_router · mqtt_bridge
├── scripts/        client_handover.py (ESP32 payload simulator) · spot_vm_bootstrap.sh
├── dashboard/      index.html — judge console (wave meter, partial ticker, intent cards,
│                   latency plot) — also served live by the gateway at **/dashboard**
├── tests/          deterministic unit tests (grammar, verifier math)
├── docs/           HANDOVER_PROTOCOL.md (wire contract for firmware)
└── docker-compose.yml
```

## Quick start — laptop (Windows/Linux/macOS)

```bash
cd cloud
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn serving.api_gateway:app --host 0.0.0.0 --port 8000
```

Second terminal:

```bash
curl http://localhost:8000/healthz
python scripts/client_handover.py --wav <any_speech.wav> --keyword jump --prototype random
```

Swagger UI at `http://localhost:8000/docs`. API token defaults to `dev-token`
(→ set `AGNI_API_TOKEN` everywhere outside your own machine).

## Quick start — docker (identical on VM *and* offline ground-station laptop)

```bash
cd cloud
AGNI_API_TOKEN=$(openssl rand -base64 24) docker compose up -d --build
```

Optional CUDA: install the NVIDIA Container Toolkit; CTranslate2 picks the GPU
up automatically (`device: "auto"`). CPU laptops run `base`/INT8 fine for the
single-stream demo.

## Quick start — rented spot GPU (finals demo, ~$0.25/h)

```bash
curl -O https://raw.githubusercontent.com/aswinkumaar06-a11y/SIH_MODEL/main/cloud/scripts/spot_vm_bootstrap.sh
bash spot_vm_bootstrap.sh small    # one command: docker + toolkit + clone + stack up
```

## Tests

```bash
cd cloud
python -m pytest tests -q        # grammar + verifier math; no GPU/model needed
```

## What happens on a handover

1. ESP32 holds 2.0 s snapshot + 32-float prototype → POST/MQTT (`docs/HANDOVER_PROTOCOL.md`)
2. Whisper transcribes (VAD-filtered; `no_speech` gate blocks silence hallucinations)
3. **Co-verifier** re-embeds the first 1.0 s with the frozen edge INT8 model and
   can veto (`intent.type = "blocked"`) — the anti-false-wake judge story
4. Grammar router → `command` intent, else `freeform` — firmware contract in the protocol doc

## Sessions roadmap

| Session | Content |
|---|---|
| **1** ✔ | zero-training pipeline: gateway + MQTT + verifier + router + protocol |
| **2** ✔ | data spine (fetchers, command-corpus generator, ESP32-channel augmentation), Whisper LoRA trainer + eval harnesses (**33/33 tests**, smoke-trained on CPU) — see `docs/TRAINING_RUNBOOK.md` |
| **3** ✔ | wav2vec-CTC command model + **grammar-constrained decoding** (29k-form trie), WS partial/final streaming, FLAC transport (−50% payload), 9 event streaming proven; **44/44 tests** |
| 4 | Phase-B scale runs, distillation/offline variant, soak tests, model cards |
