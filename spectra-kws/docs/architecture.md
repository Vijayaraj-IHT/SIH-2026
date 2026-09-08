# Spectra — System Architecture

## Overview

Spectra is a low-latency voice activator for edge devices. It detects the custom wake word "Spectra" on-device using a 22 KB neural network running on a ₹1,000 RISC-V microcontroller, then streams audio to a cloud ASR server over 5 GHz Wi-Fi 6.

## Design Principles

1. **Private by default** — Audio never leaves the device unless the wake word is detected
2. **Zero idle cost** — Wi-Fi and cloud are idle 99% of the time
3. **Instant feel** — Sub-800ms end-to-end latency
4. **Tiny footprint** — 22 KB model, < 40 KB RAM, fits in 384 KB SRAM

---

## System Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                        ESP32-C5 (on-device)                         │
│                                                                      │
│  ┌─────────┐   ┌──────────┐   ┌──────────┐   ┌──────────────┐      │
│  │ INMP441  │──▸│ I2S DMA  │──▸│  Ring    │──▸│   MFCC       │      │
│  │ (mic)   │   │          │   │  Buffer  │   │  Front-end   │      │
│  └─────────┘   └──────────┘   │  (500ms) │   │  (C, 3ms)    │      │
│                               └──────────┘   └──────┬───────┘      │
│                                                      │              │
│                                                      ▼              │
│                              ┌──────────────────────────────┐       │
│                              │   DS-CNN-S (INT8, 22 KB)    │       │
│                              │   TFLite Micro (~15ms)      │       │
│                              └──────────────┬───────────────┘       │
│                                              │                      │
│                                              ▼                      │
│                              ┌──────────────────────────────┐       │
│                              │   Trigger Logic              │       │
│                              │   Posterior smoothing (3w)   │       │
│                              │   Consecutive hits (2)       │       │
│                              └──────────────┬───────────────┘       │
│                                              │ spectra detected     │
│                                              ▼                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    Audio Streaming Pipeline                   │   │
│  │  Flush ring buffer (500ms) → Open WS → Stream PCM 16-bit    │   │
│  └──────────────────────────────┬───────────────────────────────┘   │
│                                  │                                   │
└──────────────────────────────────┼───────────────────────────────────┘
                                   │  5 GHz Wi-Fi 6
                                   ▼
┌──────────────────────────────────────────────────────────────────────┐
│                        Cloud Server                                  │
│                                                                      │
│  ┌────────────────┐   ┌────────────────┐   ┌────────────┐          │
│  │  WebSocket      │──▸│  faster-whisper │──▸│  Transcript│          │
│  │  Server         │   │  (Whisper ASR)  │   │  (JSON)    │          │
│  └────────────────┘   └────────────────┘   └────────────┘          │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. Audio Capture (I2S DMA)

**Hardware**: INMP441 digital MEMS microphone connected via I2S bus.

**Configuration**:
- Sample rate: 16 kHz
- Bit depth: 16-bit
- Format: I2S Philips standard
- Channels: Mono (left channel)

**Implementation**: I2S DMA writes samples directly to a ring buffer in SRAM. The CPU is not involved in the copy — this is the "zero-cost" capture stage.

**Ring buffer sizing**:
- **Ring buffer**: 1 second (16,000 samples × 2 bytes = 32 KB). Must be ≥ MFCC window duration.
- **Flush window**: 500 ms (8,000 samples × 2 bytes = 16 KB). The most recent 500ms of the ring buffer, sent to ASR on trigger.
- **DMA transfer buffer**: 1,024 samples (2 KB). Filled by hardware every ~64ms.

> **Why 1 second, not 500ms?** The MFCC front-end needs a full 1-second window to produce 49 frames. The 500ms "flush" is just the most recent half of the 1-second ring buffer — sent to the ASR server so the first syllable after "Spectra" is never lost.

**Pin mapping** (XIAO ESP32-C5):
| INMP441 Pin | ESP32-C5 Pin | Function |
|---|---|---|
| SCK | GPIO 7 | I2S Serial Clock |
| WS | GPIO 8 | I2S Word Select |
| SD | GPIO 9 | I2S Serial Data |
| VDD | 3.3V | Power |
| GND | GND | Ground |
| L/R | GND | Left channel |

### 2. MFCC Feature Extraction

**Pipeline** (runs every 200 ms):
1. Read last 1 second of audio from ring buffer
2. Pre-emphasis: y[n] = x[n] - 0.97 × x[n-1]
3. Framing: 25 ms windows, 10 ms hop → 98 frames
4. Hamming window
5. 256-point FFT → power spectrum
6. 40-band Mel filterbank (60–7800 Hz)
7. Log(energy) per band
8. DCT-II → keep first 13 coefficients
9. Select first 10 features per frame
10. Centre-crop to 49 frames
11. Per-utterance normalisation (zero mean, unit variance)

**Output**: (49, 10) float32 matrix

**Latency**: ~3 ms on ESP32-C5 @ 240 MHz (using ESP-DSP FFT)

**Bit-exactness**: The C implementation must produce identical output to the Python reference (`features.py`). Validation is done by comparing feature matrices from both implementations on the same audio.

### 3. DS-CNN-S Model

**Architecture**: Depthwise-Separable CNN (small variant)

```
Input: (1, 49, 10)

Conv2D(64, 3×3) + BN + ReLU
DS-Block(64→64, s=1)
DS-Block(64→64, s=2)    ← downsample
DS-Block(64→96, s=1)
DS-Block(96→96, s=2)    ← downsample
DS-Block(96→128, s=1)
GlobalAveragePooling2D
FC(128→3)

Output: [spectra, unknown, silence]
```

**Parameter count**: ~22,000
**Model size (INT8)**: ~22 KB
**Inference RAM**: < 40 KB (tensor arena)
**Inference time**: < 20 ms on ESP32-C5 @ 240 MHz

**Why DS-CNN?**
- Depthwise-separable convolutions: ~8× fewer parameters than standard convolutions
- Global average pooling: tolerant to word position in the window
- All ops are INT8-quantisation friendly

### 4. Trigger Logic

**Strategy**: Posterior smoothing + consecutive hit detection.

```
For each inference (every 200ms):
  1. Get P(spectra) from model
  2. Add to circular buffer (last 3 windows)
  3. Compute EMA-smoothed score
  4. If smoothed_score > θ (0.70):
       consecutive_hits++
  5. Else:
       consecutive_hits = 0
  6. If consecutive_hits ≥ 2:
       → TRIGGER!
       → Enter 2s cooldown
```

This turns a noisy per-frame classifier into a reliable binary switch with very few false alarms.

**Tuning**:
- Lower θ → more sensitive, more false accepts
- Higher θ → more robust, more false rejects
- More consecutive hits needed → more robust, higher latency
- Fewer hits → faster response, more false alarms

### 5. Audio Streaming

**Protocol**: WebSocket (binary frames for audio, text frames for control)

**Sequence after trigger**:
1. Flush 500 ms ring buffer (pre-trigger audio)
2. Send `{"cmd": "start"}` to ASR server
3. Send ring buffer as binary WebSocket frames (100 ms chunks)
4. Continue reading live audio from I2S and streaming
5. After 10s timeout: send `{"cmd": "end"}`
6. Receive `{"type": "final", "text": "..."}`
7. Display transcript
8. Return to listening

**Why flush the ring buffer?** The first syllable *after* "Spectra" might be part of the command. By sending the 500 ms before the trigger, we capture the tail end of "Spectra" + the start of the command.

### 6. ASR Server

**Technology**: faster-whisper (CTranslate2 Whisper implementation)

**Features**:
- WebSocket server (asyncio)
- Receives 16-bit PCM, 16 kHz, mono
- Runs Whisper-class ASR with VAD filtering
- Streams partial results as they arrive
- Returns final transcript

---

## Latency Budget

| Stage | Time | Notes |
|---|---|---|
| I2S DMA capture | 0 µs CPU | Hardware DMA, continuous |
| Ring buffer write | ~0 µs | Memory copy, negligible |
| MFCC extraction | ~3 ms | Per inference cycle |
| DS-CNN inference | ~15 ms | INT8 on RISC-V @ 240 MHz |
| Trigger logic | ~0.1 ms | EMA + counter |
| **Device-side total** | **~18 ms** | |
| Ring buffer flush | ~1 ms | 500 ms audio, memory copy |
| Wi-Fi connection | ~50 ms | Already connected (persistent) |
| WebSocket open | ~20 ms | TCP + WS handshake (persistent) |
| **Pre-stream overhead** | **~71 ms** | |
| Audio streaming | ~500 ms | 500 ms ring buffer + first chunk |
| ASR processing | ~300 ms | faster-whisper (base model) |
| **End-to-end total** | **< 800 ms** | From end of wake word to transcript |

---

## Memory Map

| Component | SRAM Usage | Notes |
|---|---|---|
| Ring buffer | 32 KB | 1s × 16 kHz × 2 bytes (must be ≥ MFCC window) |
| DMA read buffer | 2 KB | 1024 samples per I2S DMA transfer |
| Audio window | 32 KB | 1s copy from ring buffer for MFCC |
| Flush buffer | 16 KB | 500ms pre-trigger audio for ASR |
| MFCC scratch | ~8 KB | Frames, FFT, Mel energy, DCT |
| MFCC tables | ~24 KB | Pre-computed Hamming, fbank, DCT |
| TFLite arena | 40 KB | Model tensors + scratch |
| Feature buffer | ~2 KB | 49 × 10 × 4 bytes |
| Wi-Fi/WS stack | ~30 KB | ESP-IDF Wi-Fi + lwIP |
| FreeRTOS + tasks | ~32 KB | 8 tasks (I2S, main, Wi-Fi, event, idle, timer, IPC) |
| **Total** | **~190 KB** | **~50% of 384 KB SRAM** |

---

## Power Considerations

| State | Power | Notes |
|---|---|---|
| Idle (listening) | ~80 mW | CPU @ 240 MHz, Wi-Fi off |
| Wi-Fi active | +120 mW | Only during streaming |
| Inference | +10 mW | CPU burst every 200 ms |
| **Idle average** | **~85 mW** | Mostly sleeping between inferences |
| **Streaming** | **~210 mW** | Transient, < 10 s per activation |

---

## Wi-Fi 6 (5 GHz) Advantage

| Feature | 2.4 GHz | 5 GHz Wi-Fi 6 |
|---|---|---|
| Channel width | 20/40 MHz | 80/160 MHz |
| Congestion | High (Bluetooth, IoT) | Low |
| Latency variability | High | Low |
| Range | Better | Shorter but sufficient for indoor |

For a voice assistant where latency is the headline metric, 5 GHz provides more predictable, lower-latency connections — critical for the "instant feel" target.
