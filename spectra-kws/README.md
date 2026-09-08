# Spectra — Low-Latency Voice Activator for Edge Devices

> SIH 2026 · Problem Statement 26172  
> "Hey Google" on a ₹1,000 RISC-V chip — private by default, near-zero idle bandwidth, sub-500 ms end-to-end.

---

## Architecture at a glance

```
INMP441 ─I²S/DMA─► 500 ms ring buffer ─► MFCC front-end ─► DS-CNN (INT8) ─► posterior smoothing
                                                                                     │
                                                                          "Spectra" detected?  yes
                                                                                     │
     flush ring buffer ─► open WebSocket over 5 GHz Wi-Fi ─► stream live audio ─► cloud ASR ─► transcript
```

| Stage | Runs on | Latency budget |
|---|---|---|
| I²S DMA capture | ESP32-C5 hardware | 0 µs CPU |
| MFCC extraction | ESP32-C5 CPU | < 5 ms / frame |
| DS-CNN inference | ESP32-C5 CPU (TFLite Micro) | < 20 ms |
| Trigger logic | ESP32-C5 CPU | < 1 ms |
| Ring-buffer flush + WS open | ESP32-C5 + Wi-Fi 6 | ~50 ms |
| Cloud ASR first token | Server (Whisper-class) | 300–500 ms |
| **Total end-to-end** | | **< 800 ms** |

---

## Repository layout

```
spectra-kws/
├── features.py              # Python MFCC front-end (reference implementation)
├── train.py                 # DS-CNN-S training pipeline
├── export_tflite.py         # INT8 quantisation → .tflite + C header
├── evaluate.py              # Offline accuracy & latency evaluation
├── augmentation.py          # Audio augmentation pipeline
├── requirements.txt         # Python dependencies
│
├── server/
│   ├── asr_server.py        # faster-whisper WebSocket ASR server
│   └── requirements.txt     # Server dependencies
│
├── firmware/                # ESP-IDF project for XIAO ESP32-C5
│   ├── CMakeLists.txt
│   ├── sdkconfig.defaults
│   ├── main/
│   │   ├── CMakeLists.txt
│   │   ├── idf_component.yml
│   │   ├── main.c
│   │   ├── spectra_config.h    # All tuning knobs in one place
│   │   ├── i2s_capture.{h,c}   # I²S DMA ring-buffer capture
│   │   ├── mfcc.{h,c}          # C MFCC front-end (bit-matches Python)
│   │   ├── kws_engine.{h,c}    # TFLite Micro inference wrapper
│   │   ├── trigger_logic.{h,c} # Posterior smoothing & firing
│   │   └── ws_stream.{h,c}     # WebSocket audio streaming
│   └── models/
│       └── spectra_model.h     # TFLite model as C byte array (generated)
│
├── dataset/
│   ├── README.md            # Data collection & organisation guide
│   ├── positives/           # "Spectra" recordings (4 conditions)
│   ├── negatives/           # Google Speech Commands (35 words)
│   ├── confusion/           # "spectrum", "expect", "extra", etc.
│   └── background/          # Ambient noise recordings
│
└── docs/
    ├── architecture.md      # Detailed system design
    └── latency_budget.md    # Full latency breakdown
```

---

## Quick start

### 1. Python environment (training & evaluation)

```bash
cd spectra-kws
pip install -r requirements.txt
```

### 2. Prepare dataset

```bash
# Download Google Speech Commands v2 for negatives
python -c "import datasets; ds = datasets.load_dataset('speech_commands','v0.02')"

# Place your "Spectra" recordings in dataset/positives/
# See dataset/README.md for the 4-condition recording matrix
```

### 3. Train

```bash
python train.py \
  --data_dir dataset \
  --epochs 100 \
  --batch_size 64 \
  --output_dir checkpoints/
```

### 4. Export to TFLite INT8

```bash
python export_tflite.py \
  --checkpoint checkpoints/best.pt \
  --output firmware/models/spectra_model.h
```

### 5. Flash firmware

```bash
cd firmware
idf.py set-target esp32c5
idf.py build flash monitor
```

### 6. Start ASR server

```bash
cd server
pip install -r requirements.txt
python asr_server.py --host 0.0.0.0 --port 8765
```

---

## Key metrics targets

| Metric | Target |
|---|---|
| Wake-word latency (end of word → trigger) | < 300 ms |
| End-to-end latency (end of word → first transcript) | < 800 ms |
| False-reject rate | < 5 % |
| False-accept rate | < 1 per 10 hours |
| Model size (flash) | ~22 KB |
| Inference RAM | < 40 KB |
| Inference time | < 20 ms |

---

## Hardware

| Component | Role | Key specs |
|---|---|---|
| Seeed XIAO ESP32-C5 | MCU | RISC-V @ 240 MHz, 384 KB SRAM, Wi-Fi 6 (2.4 + 5 GHz), BLE |
| INMP441 | Microphone | Digital MEMS, I²S, 24-bit, ~61 dB SNR |
| Cloud server | ASR | Any machine running faster-whisper behind WebSocket |

---

## References

- **Hello Edge** (Zhang et al.) — DS-CNN architecture for keyword spotting
- **MobileNets** (Howard et al.) — Depthwise-separable convolutions
- **Quantization (Jacob et al.)** — INT8 post-training quantisation
- **TensorFlow Lite Micro** — On-device inference runtime
- **Speech Commands Dataset** (Warden) — Negative keyword source

---

## License

This project is developed for Smart India Hackathon 2026 (PS 26172).
