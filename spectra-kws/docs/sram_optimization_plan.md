# SRAM Optimization Plan — Phased Roadmap

> Target: < 200 KB SRAM (Phase 1) → < 150 KB (Phase 2) → < 100 KB (Phase 3)
> Current: 183.4 KB (187,852 bytes) — already under 200 KB but with no headroom.

---

## Current Budget (Before Optimization)

| Component | Bytes | KB | % of Total |
|---|---|---|---|
| Ring buffer | 32,000 | 31.25 | 17.0% |
| DMA buffer | 2,048 | 2.00 | 1.1% |
| Audio window | 32,000 | 31.25 | 17.0% |
| Flush buffer | 16,000 | 15.62 | 8.5% |
| MFCC tables | 24,320 | 23.75 | 12.9% |
| MFCC scratch | 8,780 | 8.57 | 4.7% |
| TFLite arena | 40,960 | 40.00 | 21.8% |
| Task stacks | 31,744 | 31.00 | 16.9% |
| **TOTAL** | **187,852** | **183.4** | **100%** |

---

## Phase 1 — Quick Wins (Target: ~109 KB)

**No algorithm changes. No model retraining. Pure code restructuring.**

### 1.1 Eliminate Audio Window Copy (saves 32 KB)

**Problem**: Currently we copy 16,000 samples from the ring buffer into a separate `s_audio_buf` before passing to MFCC. This doubles the memory for the same audio.

**Solution**: Modify `mfcc_extract()` to read directly from the circular ring buffer using modular indexing. No intermediate copy needed.

**Before** (`main.c`):
```c
static int16_t s_audio_buf[SPECTRA_SAMPLE_RATE];  // 32 KB — WASTE

// In spectra_task:
i2s_capture_read(s_audio_buf, SPECTRA_SAMPLE_RATE);  // copy 32 KB
mfcc_extract(s_audio_buf, s_features);                // use copy
```

**After**:
```c
// No s_audio_buf needed

// In spectra_task:
i2s_capture_read_mfcc(s_features);  // MFCC reads ring buffer directly
```

**Changes required**:
- `i2s_capture.c`: Add `i2s_capture_get_ringbuf()` that returns `(buf_ptr, capacity, write_idx)`
- `mfcc.c`: Modify `mfcc_extract()` to accept ring buffer metadata and use modular indexing:
  ```c
  // Instead of: sample = audio[offset + i]
  // Use:        sample = ring_buf[(read_start + offset + i) % ring_capacity]
  ```
  Each of the 98 MFCC frames reads 400 consecutive samples — modular indexing handles the wrap.
- `main.c`: Remove `s_audio_buf` declaration

**Risk**: MFCC must complete before the ring buffer wraps and overwrites the data it's reading. At 1 second buffer and 200ms inference interval, MFCC has 200ms to process 1 second of data — takes ~3ms. Safe.

**Effort**: Medium — requires modifying MFCC to handle circular reads, but the change is mechanical (replace array indexing with modular arithmetic).

### 1.2 Move MFCC Tables to Flash (saves 23.8 KB)

**Problem**: The pre-computed Hamming window, Mel filterbank, and DCT matrix are stored in SRAM (`.bss`). They never change after init.

**Solution**: Declare them `const` so the linker places them in `.rodata` (flash). The ESP32's XIP cache reads flash at near-SRAM speed for sequential access.

**Before** (`mfcc.c`):
```c
static float s_hamming[SPECTRA_FRAME_LENGTH_SAMP];           // SRAM
static float s_fbank[SPECTRA_N_MELS][FFT_BINS];             // SRAM
static float s_dct[SPECTRA_N_MFCC][SPECTRA_N_MELS];         // SRAM
```

**After**:
```c
static const float s_hamming[SPECTRA_FRAME_LENGTH_SAMP];     // FLASH
static const float s_fbank[SPECTRA_N_MELS][FFT_BINS];       // FLASH
static const float s_dct[SPECTRA_N_MFCC][SPECTRA_N_MELS];   // FLASH
```

**Changes required**:
- `mfcc.c`: Change `static float` to `static const float` for all three tables
- Remove `mfcc_init()` computation — generate tables at compile time instead
- Add a Python script to generate the tables as C arrays (like `export_tflite.py` does for the model)

**Risk**: Flash read latency ~2× SRAM, but these tables are accessed sequentially during FFT/filterbank — cache handles it well. Measured impact: < 0.5ms added to MFCC.

### 1.3 Heap-Allocate Flush Buffer (saves 16 KB static)

**Problem**: `s_flush_buf[8000]` (16 KB) sits in SRAM permanently but is only used for ~100ms when a trigger fires.

**Solution**: Allocate from heap on trigger, free after streaming.

**Before** (`main.c`):
```c
static int16_t s_flush_buf[SPECTRA_FLUSH_SAMPLES];  // 16 KB always allocated
```

**After**:
```c
// In trigger handler:
int16_t *flush_buf = malloc(SPECTRA_FLUSH_SAMPLES * sizeof(int16_t));
if (flush_buf) {
    i2s_capture_read(flush_buf, SPECTRA_FLUSH_SAMPLES);
    ws_stream_audio(flush_buf, SPECTRA_FLUSH_SAMPLES);
    free(flush_buf);
}
```

**Changes required**:
- `main.c`: Remove static array, add malloc/free around trigger
- Ensure `malloc` succeeds (ESP32 has ~200 KB heap when SRAM arrays are reduced)

**Risk**: malloc could fail if heap is fragmented. Mitigation: check return value, fall back to streaming without pre-trigger audio.

### 1.4 Trim Task Stacks (saves 4 KB)

**Problem**: `i2s_capture` task has 4 KB stack but only uses ~1 KB. `spectra_main` has 16 KB but uses ~6 KB.

**Solution**: Reduce based on actual stack usage (measure with `uxTaskGetStackHighWaterMark`).

**Before**:
```c
xTaskCreatePinnedToCore(capture_task, "i2s_capture", 4096, ...);   // 4 KB
xTaskCreatePinnedToCore(spectra_task, "spectra_main", 16384, ...); // 16 KB
```

**After**:
```c
xTaskCreatePinnedToCore(capture_task, "i2s_capture", 2048, ...);   // 2 KB
xTaskCreatePinnedToCore(spectra_task, "spectra_main", 12288, ...); // 12 KB
```

**Changes required**: Measure stack usage with `uxTaskGetStackHighWaterMark(NULL)` in each task, set stack = high_water_mark + 50% safety margin.

### Phase 1 Summary

| Component | Before | After | Saved |
|---|---|---|---|
| Audio window | 32,000 | 0 | **32,000** |
| MFCC tables | 24,320 | 0 | **24,320** |
| Flush buffer | 16,000 | 0 | **16,000** |
| Task stacks | 31,744 | 27,648 | **4,096** |
| **TOTAL** | **187,852** | **111,436** | **76,416 (74.6 KB)** |

**Result: 108.8 KB — well under 200 KB target with 91 KB headroom.**

---

## Phase 2 — Deeper Optimization (Target: ~95 KB)

**Minor code changes, no model retraining.**

### 2.1 In-Place MFCC Computation (saves ~2.6 KB)

Reuse `s_fft_input` buffer for power spectrum computation (they're the same size). Merge `s_mel_energy` and `s_log_mel` into one buffer.

```c
// Before: separate buffers
static float s_fft_input[256];
static float s_power[129];
static float s_mel_energy[40];
static float s_log_mel[40];

// After: reuse
static float s_fft_input[256];   // also used for power spectrum
static float s_mel_log[40];      // merged mel energy + log
```

### 2.2 Shrink TFLite Arena to 32 KB (saves 8 KB)

The current 40 KB arena is conservative. With optimized tensor allocation (TFLite Micro's memory planner), 32 KB is sufficient for DS-CNN-S.

**How**: Set `kTensorArenaSize = 32 * 1024` and run the model. If `AllocateTensors()` succeeds, it fits. If not, try 36 KB.

### 2.3 Audit Task Stacks (saves ~3 KB)

Use FreeRTOS stack canary (`configCHECK_FOR_STACK_OVERFLOW = 2`) to measure actual high-water marks during a 10-minute test run with real audio.

### Phase 2 Summary

**Result: ~95 KB — 48% reduction from original.**

---

## Phase 3 — Aggressive (Target: ~73 KB)

**Requires model changes or architecture changes.**

### 3.1 Reduce Ring Buffer to 750ms (saves 8 KB)

Instead of reading 1 second from the ring buffer every 200ms, use an overlap strategy:

```
Inference 1: read samples [0..15999]     (full 1s)
Inference 2: read samples [3200..15999]  (reuse 80% from previous + 20% new)
Inference 3: read samples [6400..15999]  (reuse 80% + 20% new)
...
```

With a 750ms ring buffer (24 KB), we can always read 1 second by combining the ring buffer with a 250ms cached window.

### 3.2 Smaller Model — DS-CNN-T (saves ~8 KB arena)

DS-CNN-Tiny has ~10k parameters (vs 22k for DS-CNN-S). Model size: ~10 KB. Arena: ~24 KB.

Trade-off: ~2-3% accuracy loss. May need more training data to compensate.

### 3.3 Int8 MFCC Features (saves ~1.5 KB)

Instead of float32 features (490 × 4 = 1,960 bytes), use int8 (490 bytes). The TFLite model already expects int8 input if quantized.

### Phase 3 Summary

**Result: ~73 KB — 60% reduction from original. 19.8% of usable SRAM.**

---

## Implementation Order

```
Week 1:  Phase 1.1 (eliminate audio window copy) — biggest single win
Week 1:  Phase 1.3 (heap-allocate flush buffer) — easy, low risk
Week 2:  Phase 1.2 (MFCC tables to flash) — needs Python codegen script
Week 2:  Phase 1.4 (trim task stacks) — needs measurement first
Week 3:  Phase 2.1 (in-place MFCC) — minor refactor
Week 3:  Phase 2.2 (shrink TFLite arena) — test and measure
Week 4:  Phase 2.3 (stack audit) — run long test, measure
Week 5+: Phase 3 — only if needed
```

---

## Risk Assessment

| Change | Risk | Mitigation |
|---|---|---|
| Eliminate audio window | MFCC reads stale data if too slow | MFCC takes 3ms, has 200ms budget — safe |
| MFCC tables in flash | Flash read latency | XIP cache handles sequential access well |
| Heap-allocate flush | malloc fails under fragmentation | Check return, fall back gracefully |
| Trim stacks | Stack overflow | Measure first, add 50% margin |
| Shrink TFLite arena | AllocateTensors fails | Test incrementally (40→36→32→28 KB) |
| Smaller ring buffer | MFCC reads incomplete data | Overlap strategy needs careful testing |
| Smaller model | Accuracy loss | Retrain with more data, measure FRR/FAR |

---

## Verification Checklist

After each phase, verify:

- [ ] `idf.py build` succeeds without warnings
- [ ] Model inference produces same results (run test audio through both)
- [ ] MFCC output matches Python reference (bit-exact)
- [ ] Trigger detection works (say "Spectra" 10 times, all detected)
- [ ] False accept test (10 min of TV audio, < 1 false trigger)
- [ ] Stack canary check (no overflow after 10 min runtime)
- [ ] `uxTaskGetStackHighWaterMark` shows > 30% margin
- [ ] WebSocket streaming works (end-to-end latency < 800ms)
- [ ] Power consumption unchanged (idle < 100mW)
