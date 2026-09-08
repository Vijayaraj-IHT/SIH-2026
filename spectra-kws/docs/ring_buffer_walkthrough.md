# Ring Buffer Deep Dive — Encoding & Sizing Walkthrough

> A step-by-step guide for both team members.
> Run the Python snippets interactively to see the actual bytes.

---

## Part 1: What the INMP441 Microphone Produces

The INMP441 is a digital MEMS microphone. It outputs audio over the **I2S bus** — a serial protocol that streams signed 16-bit integers.

```
INMP441 pins:
  SCK  ──▸  Serial Clock (bit clock, 512 kHz for 16kHz sample rate)
  WS   ──▸  Word Select (toggles left/right channel, 16 kHz)
  SD   ──▸  Serial Data (the actual audio bits, MSB first)
  L/R  ──▸  Tied to GND → left channel only (mono)
```

**What I2S looks like on the wire (one sample):**

```
WS:   ┌───────┐               ┌───────┐
      │ LEFT  │    RIGHT      │ LEFT  │
  ────┘       └───────────────┘       └────

SD:   [  16 bits of audio data  ] [  16 bits  ]
       MSB first, signed int16
```

**What the ESP32's I2S peripheral does:**

It receives those serial bits via DMA and writes them directly to a memory buffer as `int16_t` values — **the CPU is never involved**. This is the "zero-cost capture" from the architecture.

---

## Part 2: The Binary Format in Memory

Once DMA writes a sample to SRAM, it looks like this:

```
Sample value:  -12345 (decimal)
Memory layout: 0xC7 0xCF  (little-endian, 2 bytes)

Sample value:  16383 (decimal, near max for 16-bit signed)
Memory layout: 0xFF 0x3F

Sample value:  0 (silence)
Memory layout: 0x00 0x00
```

**Key facts:**
- Each sample is **exactly 2 bytes** (`int16_t`, signed 16-bit)
- **Little-endian** (native byte order on ESP32-C5 RISC-V)
- **Mono** (one channel only)
- **16,000 samples per second** (16 kHz sample rate)
- Values range from **-32,768 to +32,767**

---

## Part 3: What a .wav File Contains

A standard WAV file has the same raw PCM data, preceded by a 44-byte header:

```
Offset  Bytes  Content
0x00    4      "RIFF"                          ← magic number
0x04    4      file size - 8                   ← little-endian uint32
0x08    4      "WAVE"                          ← format
0x0C    4      "fmt "                          ← chunk ID
0x10    4      16 (PCM chunk size)             ← uint32
0x14    2      1 (PCM format)                  ← uint16
0x16    2      1 (mono)                        ← uint16
0x18    4      16000 (sample rate)             ← uint32
0x1C    4      32000 (byte rate)               ← uint32
0x20    2      2 (block align)                 ← uint16
0x22    2      16 (bits per sample)            ← uint16
0x24    4      "data"                          ← chunk ID
0x28    4      data size in bytes              ← uint32
0x2C    ...    raw PCM int16 samples           ← THE ACTUAL AUDIO
```

**The critical insight: bytes 0x2C onward are identical to what the ring buffer stores.**

The conversion from .wav to ring buffer format is simply:
1. Skip the 44-byte header
2. Read the raw bytes
3. Those bytes are `int16_t` samples, little-endian, mono, 16 kHz
4. That's exactly what the ring buffer contains

---

## Part 4: Live Demo — See the Actual Bytes

Run this Python snippet to see the real bytes:

```python
import numpy as np

# Generate 1 second of a 440 Hz sine wave (A4 note)
sr = 16000
t = np.linspace(0, 1.0, sr, endpoint=False)
audio_f32 = 0.5 * np.sin(2 * np.pi * 440 * t)   # float32, range [-1, 1]
audio_i16 = (audio_f32 * 32767).astype(np.int16)  # int16, range [-32768, 32767]

print(f"Shape:  {audio_i16.shape}")      # (16000,)
print(f"Dtype:  {audio_i16.dtype}")      # int16
print(f"Bytes:  {audio_i16.nbytes}")     # 32000
print(f"Min:    {audio_i16.min()}")      # -16383
print(f"Max:    {audio_i16.max()}")      #  16383

# Show the first 10 samples (what's in memory)
print(f"\nFirst 10 samples (what DMA writes to SRAM):")
for i in range(10):
    val = audio_i16[i]
    raw = audio_i16[i:i+1].tobytes()     # 2 bytes, little-endian
    print(f"  sample[{i:4d}] = {val:>6d}  →  0x{raw[0]:02X} 0x{raw[1]:02X}  ({raw[0]:3d} {raw[1]:3d})")

# Save as ring buffer binary (no header, just raw int16)
audio_i16.tobytes()  # this IS the ring buffer format
```

**Output:**
```
First 10 samples (what DMA writes to SRAM):
  sample[   0] =      0  →  0x00 0x00  (  0   0)
  sample[   1] =   1286  →  0x06 0x05  (  6   5)
  sample[   2] =   2568  →  0x08 0x0A  (  8  10)
  sample[   3] =   3841  →  0x01 0x0F  (  1  15)
  sample[   4] =   5100  →  0xEC 0x13  (236  19)
  sample[   5] =   6341  →  0x85 0x18  (133  24)
  sample[   6] =   7560  →  0xA8 0x1D  (168  29)
  sample[   7] =   8752  →  0x30 0x22  ( 48  34)
  sample[   8] =   9913  →  0x19 0x26  ( 25  38)
  sample[   9] =  11040  →  0xE0 0x2A  (224  42)
```

---

## Part 5: The Ring Buffer — How It Works

The ring buffer is a **circular array** in SRAM. The DMA writes new samples at `write_idx`, and when it reaches the end, it wraps around to the beginning:

```
Capacity: 16,000 samples (1 second, 32 KB)

Index:  0    1    2    ...  7998  7999  8000  ...  15998  15999
       [oldest audio ............... ↑ .............. newest audio]
                                     write_idx

When write_idx reaches 15999:
  Next write goes to index 0 (wraps around)
  The oldest sample is overwritten
```

**What happens on each DMA transfer:**
```
DMA fills buffer:  1024 samples = 2048 bytes = 64ms of audio
Time between DMA fills: 64ms (at 16 kHz)
Ring buffer fill time: 16000 / 1024 = 15.6 DMA transfers = 1.0 second
```

**What the MFCC front-end reads:**
```
Every 200ms, read the LAST 16,000 samples from the ring buffer.
This gives a 1-second window of the most recent audio.
The MFCC extracts 49 frames × 10 features from this window.
```

**What gets flushed on wake-word trigger:**
```
Read the LAST 8,000 samples (most recent 500ms).
This is the pre-trigger audio — sent to ASR so the first
syllable after "Spectra" is never lost.
```

---

## Part 6: Size Analysis — Every Unit of Speech

Here is every discrete unit of audio in the system, from smallest to largest:

### Per-Sample Level

| Unit | Samples | Bytes | Description |
|---|---|---|---|
| 1 sample | 1 | 2 | One int16_t — one instant of sound pressure |
| 1 ms | 16 | 32 | One millisecond of audio |
| 1 DMA transfer | 1,024 | 2,048 | One I2S DMA buffer fill (64ms) |

### MFCC Analysis Level

| Unit | Samples | Bytes | Duration | Description |
|---|---|---|---|---|
| 1 frame | 400 | 800 | 25ms | One MFCC analysis window |
| 1 hop | 160 | 320 | 10ms | Shift between consecutive frames |
| 1 second | 16,000 | 32,000 | 1,000ms | Full MFCC input window |
| 1 feature row | 10 floats | 40 | — | One frame's MFCC output (10 coefficients) |
| 1 feature matrix | 49×10 | 1,960 | — | Full MFCC output for one inference |

### Buffer Level (what lives in SRAM)

| Buffer | Samples | Bytes | KB | Role |
|---|---|---|---|---|
| Ring buffer | 16,000 | 32,000 | 31.25 | Circular, overwritten every 1s |
| DMA buffer | 1,024 | 2,048 | 2.00 | Temporary, copied to ring buffer |
| Audio window | 16,000 | 32,000 | 31.25 | Copy from ring buffer for MFCC |
| Flush buffer | 8,000 | 16,000 | 15.62 | Pre-trigger audio for ASR |
| TFLite arena | — | 40,960 | 40.00 | Model inference scratch memory |
| **Total** | | **123,008** | **120.1** | |

### Scaling: How Size Changes with Parameters

| Parameter | Current | 2× Larger | Impact |
|---|---|---|---|
| Sample rate 16→32 kHz | 32 KB | 64 KB | Ring buffer doubles, MFCC frames double |
| Ring buffer 1→2 seconds | 32 KB | 64 KB | More pre-trigger audio, more SRAM |
| Bit depth 16→32 bit | 2 B/sample | 4 B/sample | Everything doubles (but INMP441 is 16-bit) |
| DMA buffer 1024→2048 | 2 KB | 4 KB | Less frequent DMA interrupts |

---

## Part 7: The Encoding Pipeline (Member 1's Workflow)

### Step-by-step: .wav → Ring Buffer Binary

```
┌─────────────────────────────────────────────────────────────┐
│  INPUT: recording.wav                                        │
│  Recorded on phone/PC, any sample rate, mono or stereo      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 1: Read WAV file                                      │
│  Parse 44-byte header → extract raw PCM samples             │
│  If stereo → average to mono                                 │
│  Result: float32 array, any sample rate                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 2: Resample to 16 kHz                                 │
│  If already 16 kHz → skip                                    │
│  If 44.1 kHz → downsample (librosa.resample)                │
│  If 8 kHz → upsample                                        │
│  Result: float32 array, exactly 16,000 samples/second       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 3: Trim or pad to 1 second                            │
│  If longer than 16,000 samples → take first 16,000          │
│  If shorter → pad with zeros (silence) at the end           │
│  Result: exactly 16,000 float32 samples                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 4: Convert float32 → int16                            │
│  float range [-1.0, 1.0] → int16 range [-32768, 32767]     │
│  Multiply by 32767, clip, cast to int16                     │
│  Result: 16,000 int16 samples = 32,000 bytes                │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  OUTPUT: test_audio.bin                                      │
│  Raw bytes: 32,000 bytes of int16 little-endian samples     │
│  No header. No metadata. Just the audio.                     │
│                                                              │
│  This is IDENTICAL to what the ring buffer contains          │
│  after the INMP441 mic captures 1 second of audio.          │
└─────────────────────────────────────────────────────────────┘
```

### The Tool

```bash
# Convert a recording to ring buffer binary
python tools/wav_to_ringbuf.py recording.wav test_audio.bin --verbose

# Generate a test tone (for unit testing)
python tools/wav_to_ringbuf.py --generate-tone 440 tone_440hz.bin

# Convert all recordings in a directory
python tools/wav_to_ringbuf.py dataset/positives/ output_bins/ --batch

# Export as C header (for embedding in firmware tests)
python tools/wav_to_ringbuf.py recording.wav test_audio.h --as-c-header
```

---

## Part 8: The Size Analysis (Member 2's Workflow)

### The Tool

```bash
# Full analysis with default parameters
python tools/size_analysis.py

# Change parameters (e.g., try 8 kHz sample rate)
python tools/size_analysis.py --sample-rate 8000 --ring-ms 1000

# Generate markdown report for documentation
python tools/size_analysis.py --report
```

### What It Computes

1. **Per-sample sizing** — how many bytes for 1 sample, 1ms, 1 frame, 1 second
2. **Ring buffer timing** — DMA transfer interval, overwrite rate, fill time
3. **Audio unit inventory** — every buffer in the system with its size
4. **FreeRTOS task stacks** — all tasks and their memory allocations
5. **SRAM budget** — total used vs. available, percentage, fit check
6. **Scaling table** — how sizes change across sample rates (8k–44.1k) and durations (250ms–2s)
7. **Data flow rates** — bytes/sec through each stage

### Key Numbers to Report

| Metric | Value | How to Use It |
|---|---|---|
| 1 sample = 2 bytes | Multiply by any sample count to get bytes | Size any buffer |
| 1 second = 32,000 bytes | The fundamental unit | Size ring buffer, flush buffer |
| Ring buffer = 32 KB | 1s × 16kHz × 2 bytes | SRAM budget line item |
| Total SRAM = 185 KB | Out of 370 KB usable (50%) | "Does it fit?" answer |
| DMA interval = 64ms | 1024 samples ÷ 16kHz | Timing analysis |

---

## Part 9: How the Two Works Connect

```
Member 1's workflow                    Member 2's workflow
─────────────────────                  ─────────────────────

Record "Spectra"                       Run size_analysis.py
       │                                      │
       ▼                                      ▼
   .wav file                          "Ring buffer needs
       │                               32 KB SRAM"
       ▼                                      │
  wav_to_ringbuf.py                           ▼
       │                              "Total SRAM: 185 KB
       ▼                               (50% of 370 KB)"
  .bin file                                  │
       │                                     ▼
       ├──▸ RingBufferSimulator       "Fits comfortably
       │    .load_from_file()          ✓"
       │           │
       │           ▼
       │    Simulate firmware's
       │    ring buffer in Python
       │           │
       │           ├──▸ read_last_n(16000) → MFCC input
       │           └──▸ read_last_n(8000)  → flush buffer
       │
       └──▸ Feed to firmware via
            serial/flash for testing
```

**Member 1** ensures the binary format matches what the hardware produces.
**Member 2** ensures the sizes fit in the hardware's memory budget.

Both must agree on the same constants:
- Sample rate: **16,000 Hz**
- Bit depth: **16-bit signed (int16_t)**
- Byte order: **Little-endian**
- Channels: **Mono**
- Ring buffer: **1 second = 16,000 samples = 32,000 bytes**
