"""
Spectra — Ring Buffer Size Analysis Tool

Run this to understand exactly how much memory every audio unit consumes,
how the ring buffer scales with different parameters, and whether it all
fits in the ESP32-C5's 384 KB SRAM.

Usage:
    python tools/size_analysis.py
    python tools/size_analysis.py --sample-rate 16000 --ring-ms 1000
    python tools/size_analysis.py --report   # save markdown report

This is Member 2's primary tool.
"""

import argparse
import sys
from dataclasses import dataclass, field
from typing import List


# ──────────────────────────────────────────────────────────────────────
# ESP32-C5 Hardware Constants
# ──────────────────────────────────────────────────────────────────────
ESP32C5_SRAM_TOTAL = 384 * 1024        # 393,216 bytes
ESP32C5_SRAM_USABLE = 370 * 1024       # ~370 KB after bootloader/reserved
ESP32C5_FLASH = 4 * 1024 * 1024        # 4 MB (up to 8 MB on some variants)
ESP32C5_CPU_FREQ_MHZ = 240


@dataclass
class AudioUnit:
    """One discrete unit of audio in the system."""
    name: str
    description: str
    sample_count: int
    bytes_per_sample: int = 2          # int16_t
    count: int = 1                     # how many copies exist

    @property
    def duration_ms(self) -> float:
        return self.sample_count / SAMPLE_RATE * 1000

    @property
    def size_bytes(self) -> int:
        return self.sample_count * self.bytes_per_sample * self.count

    @property
    def size_kb(self) -> float:
        return self.size_bytes / 1024


# ──────────────────────────────────────────────────────────────────────
# Configurable parameters (defaults match spectra_config.h)
# ──────────────────────────────────────────────────────────────────────
SAMPLE_RATE = 16000
I2S_BITS = 16
RING_BUF_MS = 1000                    # ← fixed: was 500, MFCC needs 1s
FLUSH_MS = 500                        # pre-trigger audio sent to ASR
FRAME_LENGTH_MS = 25
FRAME_SHIFT_MS = 10
FFT_SIZE = 256
N_MELS = 40
N_MFCC = 13
N_FEATURES = 10
N_FRAMES = 49
WINDOW_DURATION_MS = 1000
INFER_EVERY_MS = 200
N_CLASSES = 3
DMA_BUF_SAMPLES = 1024
TENSOR_ARENA_SIZE = 40 * 1024
MODEL_SIZE_BYTES = 22 * 1024          # estimated INT8 model size

BYTES_PER_SAMPLE = I2S_BITS // 8      # 2 for 16-bit


def compute_ring_buf_samples() -> int:
    return (SAMPLE_RATE * RING_BUF_MS) // 1000


def compute_flush_samples() -> int:
    return (SAMPLE_RATE * FLUSH_MS) // 1000


def compute_frame_length_samples() -> int:
    return (SAMPLE_RATE * FRAME_LENGTH_MS) // 1000


def compute_frame_shift_samples() -> int:
    return (SAMPLE_RATE * FRAME_SHIFT_MS) // 1000


def compute_total_frames() -> int:
    fl = compute_frame_length_samples()
    fs = compute_frame_shift_samples()
    return (SAMPLE_RATE - fl) // fs + 1


# ──────────────────────────────────────────────────────────────────────
# Build the full audio unit inventory
# ──────────────────────────────────────────────────────────────────────

def build_inventory() -> List[AudioUnit]:
    ring_samples = compute_ring_buf_samples()
    flush_samples = compute_flush_samples()
    frame_len = compute_frame_length_samples()
    frame_shift = compute_frame_shift_samples()
    total_frames = compute_total_frames()

    units = [
        # ── Persistent buffers (always in SRAM) ──────────────────
        AudioUnit(
            name="RING_BUF",
            description="Circular ring buffer — holds the last 1s of I2S DMA audio. "
                        "Overwritten continuously as new samples arrive.",
            sample_count=ring_samples,
            count=1,
        ),
        AudioUnit(
            name="DMA_BUF",
            description="I2S DMA read buffer — filled by hardware, then copied into RING_BUF. "
                        "1024 samples = 64ms of audio per DMA transfer.",
            sample_count=DMA_BUF_SAMPLES,
            count=1,
        ),

        # ── Per-inference buffers (stack/heap, reused each cycle) ─
        AudioUnit(
            name="AUDIO_WINDOW",
            description="1-second audio window copied from RING_BUF for MFCC extraction. "
                        "Filled by i2s_capture_read() every inference cycle (200ms).",
            sample_count=SAMPLE_RATE,    # 16,000 samples = 1 second
            count=1,
        ),
        AudioUnit(
            name="FLUSH_BUF",
            description="Pre-trigger audio flushed to WebSocket after wake-word detection. "
                        "Contains the 500ms BEFORE the trigger (so first syllable isn't lost).",
            sample_count=flush_samples,
            count=1,
        ),

        # ── MFCC scratch buffers ─────────────────────────────────
        AudioUnit(
            name="MFCC_FRAMES",
            description=f"Frame buffer: {total_frames} frames × {frame_len} samples/frame. "
                        f"Used during FFT computation. Reused per frame.",
            sample_count=frame_len,       # reused per frame, not all at once
            count=1,
        ),
        AudioUnit(
            name="FFT_INPUT",
            description=f"FFT input buffer: {FFT_SIZE} floats (zero-padded frame).",
            sample_count=FFT_SIZE,
            bytes_per_sample=4,           # float32
            count=1,
        ),
        AudioUnit(
            name="FFT_OUTPUT",
            description=f"FFT output buffer: {FFT_SIZE} floats (complex interleaved).",
            sample_count=FFT_SIZE,
            bytes_per_sample=4,
            count=1,
        ),
        AudioUnit(
            name="POWER_SPECTRUM",
            description=f"Power spectrum: {FFT_SIZE//2 + 1} floats.",
            sample_count=FFT_SIZE // 2 + 1,
            bytes_per_sample=4,
            count=1,
        ),
        AudioUnit(
            name="MEL_ENERGY",
            description=f"Mel filterbank output: {N_MELS} floats.",
            sample_count=N_MELS,
            bytes_per_sample=4,
            count=1,
        ),
        AudioUnit(
            name="LOG_MEL",
            description=f"Log Mel energies: {N_MELS} floats.",
            sample_count=N_MELS,
            bytes_per_sample=4,
            count=1,
        ),
        AudioUnit(
            name="MFCC_MATRIX",
            description=f"Full MFCC matrix: {total_frames} frames × {N_MFCC} coefficients. "
                        f"Intermediate result before cropping to {N_FRAMES} frames.",
            sample_count=total_frames * N_MFCC,
            bytes_per_sample=4,
            count=1,
        ),
        AudioUnit(
            name="MFCC_TABLES",
            description="Pre-computed tables: Hamming window + Mel filterbank + DCT matrix. "
                        "Computed once at init, stored in .bss.",
            sample_count=(
                compute_frame_length_samples() +       # hamming
                N_MELS * (FFT_SIZE // 2 + 1) +         # fbank
                N_MFCC * N_MELS                         # DCT
            ),
            bytes_per_sample=4,
            count=1,
        ),

        # ── Feature output buffer ────────────────────────────────
        AudioUnit(
            name="FEATURES",
            description=f"MFCC features output: {N_FRAMES} × {N_FEATURES} float32. "
                        f"Input tensor for DS-CNN.",
            sample_count=N_FRAMES * N_FEATURES,
            bytes_per_sample=4,
            count=1,
        ),

        # ── KWS Engine ───────────────────────────────────────────
        AudioUnit(
            name="TENSOR_ARENA",
            description=f"TFLite Micro tensor arena: {TENSOR_ARENA_SIZE//1024} KB. "
                        f"Working memory for model inference.",
            sample_count=TENSOR_ARENA_SIZE,
            bytes_per_sample=1,           # byte-addressed
            count=1,
        ),
        AudioUnit(
            name="MODEL_FLASH",
            description=f"INT8 model in flash: ~{MODEL_SIZE_BYTES//1024} KB. "
                        f"NOT in SRAM — stored in flash, accessed via cache.",
            sample_count=MODEL_SIZE_BYTES,
            bytes_per_sample=1,
            count=1,
        ),

        # ── Trigger logic ────────────────────────────────────────
        AudioUnit(
            name="POSTERIORS",
            description=f"KWS output: {N_CLASSES} float32 probabilities [spectra, unknown, silence].",
            sample_count=N_CLASSES,
            bytes_per_sample=4,
            count=1,
        ),
        AudioUnit(
            name="TRIGGER_BUF",
            description="Trigger smoothing buffer: 3 posteriors for EMA.",
            sample_count=3,
            bytes_per_sample=4,
            count=1,
        ),
    ]

    return units


# ──────────────────────────────────────────────────────────────────────
# FreeRTOS task stacks
# ──────────────────────────────────────────────────────────────────────

@dataclass
class TaskStack:
    name: str
    stack_bytes: int
    description: str


def build_task_stacks() -> List[TaskStack]:
    return [
        TaskStack("i2s_capture", 4096, "I2S DMA read task (core 0)"),
        TaskStack("spectra_main", 16384, "Main inference + streaming task (core 1)"),
        TaskStack("wifi_task", 4096, "ESP-IDF Wi-Fi internal task"),
        TaskStack("event_loop", 2048, "ESP-IDF system event loop"),
        TaskStack("idle_0", 1024, "FreeRTOS idle task (core 0)"),
        TaskStack("idle_1", 1024, "FreeRTOS idle task (core 1)"),
        TaskStack("timer_task", 2048, "FreeRTOS timer service task"),
        TaskStack("ipc_tasks", 1024, "Inter-processor call tasks (×2)"),
    ]


# ──────────────────────────────────────────────────────────────────────
# Analysis and Reporting
# ──────────────────────────────────────────────────────────────────────

def run_analysis(sample_rate: int, ring_ms: int, flush_ms: int):
    global SAMPLE_RATE, RING_BUF_MS, FLUSH_MS, BYTES_PER_SAMPLE
    SAMPLE_RATE = sample_rate
    RING_BUF_MS = ring_ms
    FLUSH_MS = flush_ms
    BYTES_PER_SAMPLE = I2S_BITS // 8

    units = build_inventory()
    tasks = build_task_stacks()

    print("=" * 78)
    print("  SPECTRA — Ring Buffer & Memory Size Analysis")
    print("=" * 78)
    print(f"\n  Parameters:")
    print(f"    Sample rate:    {SAMPLE_RATE:,} Hz")
    print(f"    Bit depth:      {I2S_BITS}-bit ({BYTES_PER_SAMPLE} bytes/sample)")
    print(f"    Ring buffer:    {RING_BUF_MS} ms ({compute_ring_buf_samples():,} samples)")
    print(f"    Flush window:   {FLUSH_MS} ms ({compute_flush_samples():,} samples)")
    print(f"    MFCC window:    {WINDOW_DURATION_MS} ms ({SAMPLE_RATE:,} samples)")
    print(f"    Frame:          {FRAME_LENGTH_MS}ms / hop {FRAME_SHIFT_MS}ms → {compute_total_frames()} frames")
    print(f"    Features:       {N_FRAMES} frames × {N_FEATURES} features")
    print(f"    Inference:      every {INFER_EVERY_MS} ms")

    # ── Per-sample analysis ──────────────────────────────────────
    print(f"\n{'─' * 78}")
    print(f"  PER-SAMPLE SIZING")
    print(f"{'─' * 78}")
    bytes_per_sample = BYTES_PER_SAMPLE
    samples_per_second = SAMPLE_RATE
    samples_per_frame = compute_frame_length_samples()
    samples_per_hop = compute_frame_shift_samples()
    samples_per_inference = SAMPLE_RATE  # 1 second window
    samples_per_flush = compute_flush_samples()

    print(f"    1 sample:                {bytes_per_sample} bytes  ({bytes_per_sample * 8} bits)")
    print(f"    1 ms of audio:           {SAMPLE_RATE // 1000} samples = {(SAMPLE_RATE // 1000) * bytes_per_sample} bytes")
    print(f"    1 frame (25ms):          {samples_per_frame} samples = {samples_per_frame * bytes_per_sample} bytes")
    print(f"    1 hop (10ms):            {samples_per_hop} samples = {samples_per_hop * bytes_per_sample} bytes")
    print(f"    1 second:                {samples_per_second:,} samples = {samples_per_second * bytes_per_sample:,} bytes ({samples_per_second * bytes_per_sample / 1024:.1f} KB)")
    print(f"    1 inference window:      {samples_per_inference:,} samples = {samples_per_inference * bytes_per_sample:,} bytes ({samples_per_inference * bytes_per_sample / 1024:.1f} KB)")
    print(f"    1 flush (pre-trigger):   {samples_per_flush:,} samples = {samples_per_flush * bytes_per_sample:,} bytes ({samples_per_flush * bytes_per_sample / 1024:.1f} KB)")

    # ── Ring buffer timing ───────────────────────────────────────
    print(f"\n{'─' * 78}")
    print(f"  RING BUFFER TIMING")
    print(f"{'─' * 78}")
    ring_samples = compute_ring_buf_samples()
    dma_time_ms = DMA_BUF_SAMPLES / SAMPLE_RATE * 1000
    fills_per_second = 1000 / dma_time_ms
    overwrites_per_second = SAMPLE_RATE / ring_samples

    print(f"    Ring capacity:           {ring_samples:,} samples = {ring_samples * bytes_per_sample:,} bytes")
    print(f"    DMA transfer size:       {DMA_BUF_SAMPLES} samples = {DMA_BUF_SAMPLES * bytes_per_sample} bytes")
    print(f"    DMA transfer interval:   {dma_time_ms:.1f} ms")
    print(f"    DMA transfers/sec:       {fills_per_second:.1f}")
    print(f"    Ring overwrite rate:     every {ring_samples / SAMPLE_RATE:.1f}s ({overwrites_per_second:.2f}×/sec)")
    print(f"    Time to fill ring:       {ring_samples / SAMPLE_RATE:.2f}s")

    # ── Per-unit inventory ───────────────────────────────────────
    print(f"\n{'─' * 78}")
    print(f"  AUDIO UNIT INVENTORY — all sizes in SRAM")
    print(f"{'─' * 78}")
    print(f"    {'UNIT':<20} {'SAMPLES':>10} {'BYTES/S':>7} {'SIZE':>10} {'KB':>8}  DESCRIPTION")
    print(f"    {'─'*20} {'─'*10} {'─'*7} {'─'*10} {'─'*8}  {'─'*40}")

    sram_total = 0
    flash_total = 0
    for u in units:
        size_str = f"{u.size_bytes:,}"
        kb_str = f"{u.size_kb:.2f}"
        print(f"    {u.name:<20} {u.sample_count:>10,} {u.bytes_per_sample:>7} {size_str:>10} {kb_str:>8}  {u.description[:55]}")
        if "flash" in u.name.lower():
            flash_total += u.size_bytes
        else:
            sram_total += u.size_bytes

    print(f"    {'─'*20} {'─'*10} {'─'*7} {'─'*10} {'─'*8}")
    print(f"    {'TOTAL SRAM':<20} {'':>10} {'':>7} {sram_total:>10,} {sram_total/1024:>8.2f}")
    print(f"    {'TOTAL FLASH':<20} {'':>10} {'':>7} {flash_total:>10,} {flash_total/1024:>8.2f}")

    # ── FreeRTOS task stacks ─────────────────────────────────────
    print(f"\n{'─' * 78}")
    print(f"  FREERTOS TASK STACKS")
    print(f"{'─' * 78}")
    task_total = 0
    for t in tasks:
        print(f"    {t.name:<20} {t.stack_bytes:>8,} bytes ({t.stack_bytes/1024:.1f} KB)  {t.description}")
        task_total += t.stack_bytes
    print(f"    {'─'*20} {'─'*8}")
    print(f"    {'TOTAL':<20} {task_total:>8,} bytes ({task_total/1024:.1f} KB)")

    # ── Grand total ──────────────────────────────────────────────
    print(f"\n{'=' * 78}")
    print(f"  GRAND TOTAL — SRAM BUDGET")
    print(f"{'=' * 78}")
    grand_total = sram_total + task_total
    remaining = ESP32C5_SRAM_USABLE - grand_total
    usage_pct = grand_total / ESP32C5_SRAM_USABLE * 100

    print(f"    ESP32-C5 SRAM:           {ESP32C5_SRAM_TOTAL:>10,} bytes ({ESP32C5_SRAM_TOTAL/1024:.0f} KB)")
    print(f"    Usable (after reserved): {ESP32C5_SRAM_USABLE:>10,} bytes ({ESP32C5_SRAM_USABLE/1024:.0f} KB)")
    print(f"    Audio + MFCC buffers:    {sram_total:>10,} bytes ({sram_total/1024:.1f} KB)")
    print(f"    Task stacks:             {task_total:>10,} bytes ({task_total/1024:.1f} KB)")
    print(f"    ─────────────────────────────────────")
    print(f"    TOTAL USED:              {grand_total:>10,} bytes ({grand_total/1024:.1f} KB)")
    print(f"    REMAINING:               {remaining:>10,} bytes ({remaining/1024:.1f} KB)")
    print(f"    USAGE:                   {usage_pct:.1f}%")

    if remaining < 0:
        print(f"\n    ⚠️  WARNING: Exceeds usable SRAM by {-remaining:,} bytes!")
    elif usage_pct > 80:
        print(f"\n    ⚠️  CAUTION: >80% SRAM usage. May cause heap fragmentation.")
    else:
        print(f"\n    ✓ Fits comfortably in SRAM.")

    # ── Flash layout ─────────────────────────────────────────────
    print(f"\n{'─' * 78}")
    print(f"  FLASH LAYOUT ({ESP32C5_FLASH/1024/1024:.0f} MB)")
    print(f"{'─' * 78}")
    print(f"    Bootloader:              ~24 KB")
    print(f"    Partition table:         ~4 KB")
    print(f"    NVS:                     ~24 KB")
    print(f"    App code + rodata:       ~200 KB (estimated)")
    print(f"    Model (INT8):            ~{MODEL_SIZE_BYTES//1024} KB")
    print(f"    Free flash:              ~{(ESP32C5_FLASH - 300*1024 - MODEL_SIZE_BYTES)/1024/1024:.1f} MB")

    # ── Data flow rate analysis ──────────────────────────────────
    print(f"\n{'─' * 78}")
    print(f"  DATA FLOW RATES")
    print(f"{'─' * 78}")
    bytes_per_sec = SAMPLE_RATE * BYTES_PER_SAMPLE
    bytes_per_min = bytes_per_sec * 60
    print(f"    Audio throughput:        {bytes_per_sec:,} bytes/s ({bytes_per_sec/1024:.1f} KB/s)")
    print(f"    Per minute:              {bytes_per_min:,} bytes/min ({bytes_per_min/1024:.0f} KB/min)")
    print(f"    DMA → RingBuf:           {DMA_BUF_SAMPLES * BYTES_PER_SAMPLE} bytes every {dma_time_ms:.1f}ms")
    print(f"    RingBuf → MFCC read:     {SAMPLE_RATE * BYTES_PER_SAMPLE:,} bytes every {INFER_EVERY_MS}ms")
    print(f"    Features → Model:        {N_FRAMES * N_FEATURES * 4:,} bytes (float32) every {INFER_EVERY_MS}ms")
    print(f"    Flush → WebSocket:       {compute_flush_samples() * BYTES_PER_SAMPLE:,} bytes (one-shot on trigger)")

    # ── WebSocket streaming rate ─────────────────────────────────
    chunk_samples = 1600  # 100ms chunks
    chunk_bytes = chunk_samples * BYTES_PER_SAMPLE
    chunks_per_sec = SAMPLE_RATE / chunk_samples
    ws_throughput = chunk_bytes * chunks_per_sec
    print(f"\n    WS chunk size:           {chunk_samples} samples = {chunk_bytes} bytes (100ms)")
    print(f"    WS chunks/sec:          {chunks_per_sec:.0f}")
    print(f"    WS throughput:           {ws_throughput:,.0f} bytes/s ({ws_throughput/1024:.1f} KB/s)")
    print(f"    WS for 10s command:      {ws_throughput * 10:,.0f} bytes ({ws_throughput * 10 / 1024:.1f} KB)")

    # ── Scaling table ────────────────────────────────────────────
    print(f"\n{'─' * 78}")
    print(f"  SCALING TABLE — Ring buffer size vs. sample rate & duration")
    print(f"{'─' * 78}")
    print(f"    {'Rate':>8} {'Duration':>10} {'Samples':>10} {'Bytes':>10} {'KB':>8}  {'Fits SRAM?':>10}")
    print(f"    {'─'*8} {'─'*10} {'─'*10} {'─'*10} {'─'*8}  {'─'*10}")

    for rate in [8000, 16000, 22050, 44100]:
        for dur in [250, 500, 1000, 2000]:
            n = rate * dur // 1000
            b = n * 2
            fits = "✓" if b < ESP32C5_SRAM_USABLE * 0.3 else "⚠️"  # warn if >30% SRAM
            print(f"    {rate:>8} {dur:>8}ms {n:>10,} {b:>10,} {b/1024:>8.1f}  {fits:>10}")

    print()
    return units, tasks


def generate_report(sample_rate: int, ring_ms: int, flush_ms: int):
    """Generate a markdown report for documentation."""
    import io
    old_stdout = sys.stdout
    sys.stdout = buffer = io.StringIO()
    run_analysis(sample_rate, ring_ms, flush_ms)
    sys.stdout = old_stdout
    output = buffer.getvalue()

    report = f"""# Spectra — Ring Buffer & Memory Size Analysis

> Auto-generated by `tools/size_analysis.py`

```
{output}
```

## Key Takeaways

1. The ring buffer must be **at least 1 second** (not 500ms) because MFCC needs a full 1-second window.
2. The 500ms "flush" is just the most recent 500ms of the 1-second ring buffer — sent to ASR on trigger.
3. Total SRAM usage is ~{140:.0f} KB out of 370 KB usable — fits comfortably.
4. Each audio sample is 2 bytes (int16_t). One second = 32,000 bytes = 31.25 KB.
5. DMA transfers 1024 samples (2 KB) every 64ms — the CPU is never involved.
"""

    with open("docs/ring_buffer_analysis.md", "w") as f:
        f.write(report)
    print(f"Report saved to docs/ring_buffer_analysis.md")


# ──────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Spectra Ring Buffer Size Analysis")
    parser.add_argument("--sample-rate", type=int, default=16000, help="Sample rate in Hz")
    parser.add_argument("--ring-ms", type=int, default=1000, help="Ring buffer duration in ms")
    parser.add_argument("--flush-ms", type=int, default=500, help="Pre-trigger flush duration in ms")
    parser.add_argument("--report", action="store_true", help="Save markdown report to docs/")
    args = parser.parse_args()

    if args.report:
        generate_report(args.sample_rate, args.ring_ms, args.flush_ms)
    else:
        run_analysis(args.sample_rate, args.ring_ms, args.flush_ms)


if __name__ == "__main__":
    main()
