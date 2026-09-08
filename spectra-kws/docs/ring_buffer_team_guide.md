# Ring Buffer Stage — Team Division Guide

## The Big Picture

The ring buffer sits between the microphone and the AI model. It has two jobs:

```
Job A (continuous):   INMP441 → DMA → ring buffer → MFCC → model
Job B (on trigger):   ring buffer → flush → WebSocket → ASR server
```

Two people, two tasks, one buffer:

| Person | Task | Question they answer |
|---|---|---|
| **Member 1** | Encoding pipeline | "How do I turn a .wav file into the exact bytes the ring buffer stores?" |
| **Member 2** | Size analysis | "How many bytes does each piece of audio consume, and does it all fit?" |

---

## The Format Everyone Must Agree On

Before anything else, both members must lock down these constants:

```
┌─────────────────────────────────────────────────────┐
│  RING BUFFER FORMAT SPECIFICATION                    │
│                                                      │
│  Sample rate:    16,000 Hz                           │
│  Bit depth:      16-bit signed integer (int16_t)     │
│  Byte order:     Little-endian                       │
│  Channels:       Mono (one channel)                  │
│  Encoding:       PCM (no compression)                │
│  Header:         NONE (raw samples only)             │
│                                                      │
│  1 sample  = 2 bytes                                 │
│  1 second  = 16,000 samples = 32,000 bytes           │
│  Ring buf  = 1 second = 32,000 bytes (31.25 KB)      │
│  Flush buf = 500ms = 8,000 samples = 16,000 bytes    │
└─────────────────────────────────────────────────────┘
```

These constants live in `firmware/main/spectra_config.h` and are the single source of truth for both tasks.

---

## Member 1 — The Encoding Pipeline

### What you own

Converting a `.wav` file (recorded on any device, any sample rate) into a `.bin` file that is byte-for-byte identical to what the ESP32's ring buffer would contain after capturing the same audio through the INMP441 microphone.

### Why it matters

If the `.bin` file doesn't match the ring buffer format exactly, the MFCC features extracted from it won't match what the firmware computes. The model will see different inputs, and all testing becomes invalid.

### The conversion pipeline

```
Step 1: READ
    ┌──────────────────────────────────────────────┐
    │  Input:  recording.wav                        │
    │  Action: Parse 44-byte WAV header             │
    │          Read raw PCM samples                 │
    │          If stereo → average to mono           │
    │  Output: float32 array, original sample rate   │
    └──────────────────────────────────────────────┘
                        │
                        ▼
Step 2: RESAMPLE
    ┌──────────────────────────────────────────────┐
    │  Input:  float32 array, any sample rate       │
    │  Action: Resample to 16,000 Hz                │
    │          (librosa.resample or scipy.signal)    │
    │  Output: float32 array, 16,000 samples/sec    │
    └──────────────────────────────────────────────┘
                        │
                        ▼
Step 3: NORMALIZE LENGTH
    ┌──────────────────────────────────────────────┐
    │  Input:  float32 array, 16 kHz               │
    │  Action: Trim to exactly 1 second             │
    │          OR pad with zeros to 1 second         │
    │  Output: exactly 16,000 float32 samples        │
    └──────────────────────────────────────────────┘
                        │
                        ▼
Step 4: QUANTIZE
    ┌──────────────────────────────────────────────┐
    │  Input:  16,000 float32 samples (range ±1.0)  │
    │  Action: Multiply by 32767                     │
    │          Clip to [-32768, 32767]               │
    │          Cast to int16                         │
    │  Output: 16,000 int16 samples                  │
    └──────────────────────────────────────────────┘
                        │
                        ▼
Step 5: WRITE
    ┌──────────────────────────────────────────────┐
    │  Input:  16,000 int16 samples                 │
    │  Action: Write raw bytes (no header)           │
    │  Output: test_audio.bin (32,000 bytes)         │
    │                                              │
    │  This file is IDENTICAL to what the ring      │
    │  buffer stores after 1 second of capture.     │
    └──────────────────────────────────────────────┘
```

### What the output looks like (actual bytes)

```
File: test_audio.bin (32,000 bytes, no header)

Offset  Bytes              What it means
0x0000  0x00 0x00          sample[0] = 0 (silence at start)
0x0002  0x00 0x0B          sample[1] = 2816 (sound pressure rising)
0x0004  0xAD 0x15          sample[2] = 5549
0x0006  0xB5 0x1F          sample[3] = 8117
...
0x7FFC  0xFD 0x3F          sample[15999] = 16381 (near end)
0x7FFE  (file ends here)   Total: 32,000 bytes exactly
```

### Your tool

```bash
# Basic conversion
python tools/wav_to_ringbuf.py recording.wav output.bin

# With detailed output (see every step)
python tools/wav_to_ringbuf.py recording.wav output.bin --verbose

# Generate test signals
python tools/wav_to_ringbuf.py --generate-tone 440 tone.bin
python tools/wav_to_ringbuf.py --generate-silence silence.bin

# Batch convert all recordings
python tools/wav_to_ringbuf.py dataset/positives/ output_bins/ --batch

# Export as C header (for firmware unit tests)
python tools/wav_to_ringbuf.py recording.wav test_audio.h --as-c-header
```

### How to verify your output

```python
import numpy as np

# Load your .bin file
data = np.fromfile("output.bin", dtype=np.int16)

# Check these:
assert len(data) == 16000, f"Expected 16000 samples, got {len(data)}"
assert data.dtype == np.int16, f"Expected int16, got {data.dtype}"
assert data.nbytes == 32000, f"Expected 32000 bytes, got {data.nbytes}"

print(f"✓ Format correct: {len(data)} samples, {data.nbytes} bytes")
print(f"  Range: [{data.min()}, {data.max()}]")
```

---

## Member 2 — The Size Analysis

### What you own

Determining exactly how many bytes every piece of audio consumes in the system, whether it all fits in the ESP32-C5's 384 KB SRAM, and how the sizes change with different parameters.

### Why it matters

The ESP32-C5 has 384 KB SRAM total. If any component is too large, the system crashes. If the total exceeds ~370 KB (after boot reserves), it won't fit. You need to prove it fits with a clear breakdown.

### The hierarchy of audio units

Every piece of audio in the system is one of these units:

```
SMALLEST ─────────────────────────────────────────────────── LARGEST

1 sample     1 ms      1 frame    1 hop     1 DMA      1 second
   │           │          │          │         │            │
   2 bytes    32 bytes   800 bytes  320 bytes  2048 bytes   32,000 bytes
   0.0625ms   1ms        25ms       10ms       64ms         1000ms
```

### Detailed breakdown

| Unit | What it is | Samples | Bytes | Duration |
|---|---|---|---|---|
| **1 sample** | One instant of sound pressure | 1 | **2** | 0.0625 ms |
| **1 ms** | One millisecond of audio | 16 | 32 | 1 ms |
| **1 frame** | One MFCC analysis window | 400 | 800 | 25 ms |
| **1 hop** | Shift between MFCC frames | 160 | 320 | 10 ms |
| **1 DMA transfer** | One I2S DMA buffer fill | 1,024 | 2,048 | 64 ms |
| **1 chunk** | One WebSocket send unit | 1,600 | 3,200 | 100 ms |
| **1 flush** | Pre-trigger audio sent to ASR | 8,000 | 16,000 | 500 ms |
| **1 second** | Full MFCC input window | 16,000 | 32,000 | 1,000 ms |

### How to compute any size

The formula is simple:

```
bytes = samples × 2
samples = sample_rate × duration_seconds
        = 16,000 × duration_in_ms / 1000
```

Examples:
- 25ms frame: `16000 × 0.025 = 400 samples × 2 = 800 bytes`
- 500ms flush: `16000 × 0.500 = 8000 samples × 2 = 16000 bytes`
- 1s ring buffer: `16000 × 1.000 = 16000 samples × 2 = 32000 bytes`

### SRAM budget

| Component | Bytes | KB | Purpose |
|---|---|---|---|
| Ring buffer | 32,000 | 31.25 | Circular, holds last 1s of mic audio |
| DMA buffer | 2,048 | 2.00 | Temporary, hardware fills this |
| Audio window | 32,000 | 31.25 | Copy from ring buffer for MFCC |
| Flush buffer | 16,000 | 15.62 | Pre-trigger audio for ASR |
| MFCC tables | 24,320 | 23.75 | Pre-computed Hamming, filterbank, DCT |
| MFCC scratch | 8,780 | 8.57 | Frames, FFT, Mel energy, features |
| TFLite arena | 40,960 | 40.00 | Model inference working memory |
| Task stacks | 31,744 | 31.00 | FreeRTOS task stacks (8 tasks) |
| **TOTAL** | **187,852** | **183.4** | **50.1% of 370 KB usable** ✓ |

### Your tool

```bash
# Full analysis with all breakdowns
python tools/size_analysis.py

# Save as markdown report
python tools/size_analysis.py --report

# Try different parameters
python tools/size_analysis.py --sample-rate 8000 --ring-ms 1000
```

---

## How the Two Tasks Connect

```
Member 1                              Member 2
────────                              ────────

Record "Spectra"                      Run size_analysis.py
     │                                     │
     ▼                                     ▼
 .wav file                         "Ring buffer = 32 KB"
     │                             "Flush buffer = 16 KB"
     ▼                             "Total SRAM = 183 KB (50%)"
wav_to_ringbuf.py                        │
     │                                   ▼
     ▼                           "Fits in ESP32-C5 ✓"
 .bin file                              │
     │                                  │
     ├──▸ Verify format:                ├──▸ Verify sizes:
     │    16,000 samples?               │    Does 32 KB fit?
     │    int16 dtype?                  │    Does 183 KB total fit?
     │    32,000 bytes?                 │    What if we change params?
     │                                  │
     ▼                                  ▼
  Both agree: the .bin file is   Both agree: the sizes fit
  byte-identical to what the     in the ESP32's memory
  ring buffer stores             budget with headroom
     │                                  │
     └──────────┬───────────────────────┘
                │
                ▼
        Combined verification:
        "The .bin file (32 KB) fits in the ring buffer (32 KB)
         which fits in SRAM (183 KB / 370 KB = 50%)"
```

### The handoff point

Member 1 produces `.bin` files. Member 2 confirms the sizes fit. Both must agree on:

| Constant | Value | Where it's defined |
|---|---|---|
| Sample rate | 16,000 Hz | `SPECTRA_SAMPLE_RATE` |
| Bit depth | 16-bit signed | `SPECTRA_I2S_BITS` |
| Ring buffer duration | 1,000 ms | `SPECTRA_RING_BUF_MS` |
| Flush duration | 500 ms | `SPECTRA_FLUSH_MS` |
| DMA buffer size | 1,024 samples | `DMA_BUF_SAMPLES` |

These constants are in `firmware/main/spectra_config.h`. If either member changes a value, both must re-run their tools.

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────┐
│                    QUICK REFERENCE                           │
│                                                              │
│  FORMAT:  int16_t, little-endian, mono, 16 kHz, no header   │
│                                                              │
│  SIZES:                                                      │
│    1 sample    = 2 bytes                                     │
│    1 ms        = 32 bytes      (16 samples)                  │
│    1 frame     = 800 bytes     (400 samples, 25ms)           │
│    1 second    = 32,000 bytes  (16,000 samples)              │
│    Ring buffer = 32,000 bytes  (1 second)                    │
│    Flush buf   = 16,000 bytes  (500ms)                       │
│                                                              │
│  TOOLS:                                                      │
│    Member 1: python tools/wav_to_ringbuf.py in.wav out.bin   │
│    Member 2: python tools/size_analysis.py                   │
│                                                              │
│  VERIFY:                                                     │
│    np.fromfile("out.bin", dtype=np.int16) → 16000 samples    │
│                                                              │
│  SOURCE OF TRUTH: firmware/main/spectra_config.h             │
└─────────────────────────────────────────────────────────────┘
```
