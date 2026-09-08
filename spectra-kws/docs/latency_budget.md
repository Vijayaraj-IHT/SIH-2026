# Spectra — Latency Budget (Detailed)

## End-to-End Latency Breakdown

This document traces a single wake-word detection from the moment the user says "Spectra" to the moment the first ASR transcript token arrives.

---

## Timeline

```
T+0ms      User says "Spectra"
T+0–800ms  INMP441 captures audio via I2S DMA (ring buffer fills)
T+800ms    Last inference cycle BEFORE trigger
T+801ms    MFCC extraction begins (on last 1s of audio)
T+804ms    MFCC complete, features ready
T+804ms    DS-CNN inference starts
T+819ms    Inference complete, posteriors ready
T+819ms    Trigger logic: smoothed_score > θ, consecutive hits ≥ 2
T+819ms    === WAKE-WORD DETECTED ===
T+820ms    Ring buffer flush (500ms pre-trigger audio, ~1ms copy)
T+821ms    WebSocket: send {"cmd": "start"} (persistent connection, ~5ms)
T+826ms    Begin streaming ring buffer over WS (500ms audio, ~50ms network)
T+876ms    Begin streaming live audio
T+1376ms   Timeout or VAD detects end-of-speech, send {"cmd": "end"}
T+1377ms   Server begins ASR processing
T+1677ms   Server sends first partial transcript (~300ms ASR)
T+1677ms   === FIRST TRANSCRIPT TOKEN RECEIVED ===
```

---

## Latency Components

### 1. Audio Capture (Continuous, 0 CPU Cost)

| Parameter | Value |
|---|---|
| I2S DMA buffer size | 1024 samples (~64 ms) |
| Ring buffer capacity | 500 ms (8,000 samples) |
| CPU involvement | None (DMA writes directly to SRAM) |

**Contribution to wake-word latency**: 0 ms (audio is always being captured)

### 2. MFCC Feature Extraction

| Operation | Time (estimated) | Notes |
|---|---|---|
| Pre-emphasis | 0.1 ms | Simple IIR filter |
| Framing + Hamming | 0.2 ms | Memory copy + multiply |
| FFT (256-pt, 98 frames) | 1.5 ms | ESP-DSP optimised |
| Mel filterbank | 0.3 ms | Sparse matrix multiply |
| Log + DCT | 0.5 ms | Element-wise + matrix |
| Normalisation | 0.2 ms | Mean/std computation |
| **Total** | **~3 ms** | On ESP32-C5 @ 240 MHz |

### 3. DS-CNN Inference

| Operation | Time (estimated) | Notes |
|---|---|---|
| Conv2D (64, 3×3) | 1 ms | First layer |
| DS-Block × 5 | 10 ms | Depthwise + pointwise each |
| Global Avg Pool | 0.1 ms | Reduce spatial dims |
| FC + Softmax | 0.2 ms | 128→3 |
| TFLite overhead | 1 ms | Memory management |
| Quantise/dequantise | 0.5 ms | INT8 ↔ float |
| **Total** | **~15 ms** | INT8 arithmetic on RISC-V |

**Target**: < 20 ms (verified with `esp_timer` around `Invoke()`)

### 4. Trigger Logic

| Operation | Time | Notes |
|---|---|---|
| Circular buffer update | 0.01 ms | One store + index update |
| EMA computation | 0.05 ms | 3-element weighted sum |
| Threshold check | 0.01 ms | One comparison |
| **Total** | **~0.1 ms** | Negligible |

### 5. Ring Buffer Flush

| Operation | Time | Notes |
|---|---|---|
| Copy 8,000 int16 samples | ~1 ms | 16 KB memory copy |
| **Total** | **~1 ms** | |

### 6. WebSocket Communication

| Operation | Time | Notes |
|---|---|---|
| WS frame send (control) | ~5 ms | JSON command, small payload |
| WS frame send (audio) | ~50 ms | 500 ms of audio over Wi-Fi 6 |
| WS connection | 0 ms | Persistent (already open) |
| **Total** | **~55 ms** | 5 GHz Wi-Fi 6 advantage |

### 7. ASR Server Processing

| Operation | Time | Notes |
|---|---|---|
| Audio buffering | ~50 ms | Wait for enough audio |
| Whisper encoding | ~150 ms | GPU: faster, CPU: slower |
| Whisper decoding | ~100 ms | Token-by-token generation |
| WebSocket send | ~5 ms | JSON response |
| **Total** | **~300 ms** | With faster-whisper (base model) |

---

## Summary Table

| Metric | Target | Expected | How to Measure |
|---|---|---|---|
| **Wake-word latency** (end of word → trigger) | < 300 ms | ~200 ms* | `esp_timer` timestamps in firmware |
| **Device-side latency** (trigger → first WS packet) | < 100 ms | ~60 ms | Timestamps in firmware |
| **End-to-end latency** (end of word → first token) | < 800 ms | ~700 ms | Timestamps at every hop |
| **Inference time** | < 20 ms | ~15 ms | `esp_timer` around `Invoke()` |
| **MFCC time** | < 5 ms | ~3 ms | `esp_timer` around `mfcc_extract()` |

\* Wake-word latency depends on where in the 200ms inference cycle the word ends. Worst case: word ends just after an inference → waits 200ms for next. Average: ~100ms.

---

## Optimisation Strategies

### If latency is too high:

1. **Reduce inference interval** (200ms → 100ms)
   - Trade-off: 2× CPU usage, slightly higher power
   - Benefit: Reduces worst-case wake-word latency by 100ms

2. **Use a smaller Whisper model** (base → tiny)
   - Trade-off: Slightly lower ASR accuracy
   - Benefit: ~2× faster ASR processing

3. **Persistent WebSocket connection**
   - Already implemented
   - Saves ~100ms per activation (TCP + WS handshake)

4. **VAD on device** (before streaming)
   - Detect end-of-speech on device, don't wait for timeout
   - Reduces unnecessary audio streaming

5. **Audio codec** (PCM → Opus)
   - Reduces network payload by ~10×
   - Trade-off: Encoding time (~2ms), server-side decoding

### If false accepts are too high:

1. Increase θ (threshold) from 0.70 → 0.80
2. Increase consecutive hits from 2 → 3
3. Add confusion word filtering (explicit negative training)
4. Add energy-based VAD before CNN (reject silence/low-energy frames)

### If false rejects are too high:

1. Lower θ from 0.70 → 0.60
2. Reduce consecutive hits from 2 → 1 (but increases false accepts)
3. Collect more training data in the failing conditions
4. Increase augmentation diversity
