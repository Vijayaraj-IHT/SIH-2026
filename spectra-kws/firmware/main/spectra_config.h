/**
 * @file spectra_config.h
 * @brief All tuning knobs for Spectra KWS in one place.
 *
 * Changing these requires re-exporting the model if feature params change.
 * Trigger thresholds can be tuned at runtime via serial commands.
 */

#ifndef SPECTRA_CONFIG_H_
#define SPECTRA_CONFIG_H_

#include <stdint.h>

/* ── Audio Capture ───────────────────────────────────────────────── */
#define SPECTRA_SAMPLE_RATE       16000   /* Hz — must match model training */
#define SPECTRA_I2S_BITS          16      /* bits per sample (INMP441 configured) */
#define SPECTRA_RING_BUF_MS       1000    /* ring buffer: must be ≥ MFCC window (1s) */
#define SPECTRA_RING_BUF_SAMPLES  ((SPECTRA_SAMPLE_RATE * SPECTRA_RING_BUF_MS) / 1000)
#define SPECTRA_FLUSH_MS          500     /* pre-trigger audio sent to ASR on wake */
#define SPECTRA_FLUSH_SAMPLES     ((SPECTRA_SAMPLE_RATE * SPECTRA_FLUSH_MS) / 1000)

/* I2S pins for XIAO ESP32-C5 + INMP441 */
#define SPECTRA_I2S_SCK_PIN       7       /* I2S serial clock (bit clock) */
#define SPECTRA_I2S_WS_PIN        8       /* I2S word select (LRCL) */
#define SPECTRA_I2S_SD_PIN        9       /* I2S serial data (DOUT) */
#define SPECTRA_I2S_PORT          I2S_NUM_0

/* ── MFCC Feature Extraction ─────────────────────────────────────── */
#define SPECTRA_FRAME_LENGTH_MS   25      /* analysis window */
#define SPECTRA_FRAME_SHIFT_MS    10      /* hop between frames */
#define SPECTRA_FFT_SIZE          256
#define SPECTRA_N_MELS            40      /* Mel filterbank bands */
#define SPECTRA_MEL_LOW_HZ        60.0f
#define SPECTRA_MEL_HIGH_HZ       7800.0f
#define SPECTRA_N_MFCC            13      /* keep c0-c12 */
#define SPECTRA_N_FEATURES        10      /* final feature count (MFCC subset) */
#define SPECTRA_WINDOW_DURATION_S 1.0f    /* sliding window for inference */
#define SPECTRA_N_FRAMES          49      /* frames per window */

/* Derived: number of frames from 1 s of audio */
#define SPECTRA_FRAME_LENGTH_SAMP ((SPECTRA_SAMPLE_RATE * SPECTRA_FRAME_LENGTH_MS) / 1000)
#define SPECTRA_FRAME_SHIFT_SAMP  ((SPECTRA_SAMPLE_RATE * SPECTRA_FRAME_SHIFT_MS) / 1000)
#define SPECTRA_TOTAL_FRAMES      ((SPECTRA_SAMPLE_RATE - SPECTRA_FRAME_LENGTH_SAMP) / SPECTRA_FRAME_SHIFT_SAMP + 1)
/* For 1s @ 16kHz: (16000 - 400) / 160 + 1 = 98 frames */

/* ── KWS Model ──────────────────────────────────────────────────── */
#define SPECTRA_N_CLASSES          3      /* spectra, unknown, silence */
#define SPECTRA_CLASS_SPECTRA      0
#define SPECTRA_CLASS_UNKNOWN      1
#define SPECTRA_CLASS_SILENCE      2
#define SPECTRA_INFER_EVERY_MS     200    /* run inference every N ms */

/* ── Trigger Logic ──────────────────────────────────────────────── */
#define SPECTRA_TRIGGER_THRESHOLD  0.70f  /* posterior must exceed this */
#define SPECTRA_SMOOTH_WINDOWS     3      /* number of windows for smoothing */
#define SPECTRA_CONSECUTIVE_HITS   2      /* consecutive windows above θ to fire */

/* ── Wi-Fi & WebSocket ──────────────────────────────────────────── */
#define SPECTRA_WIFI_SSID          "YOUR_WIFI_SSID"
#define SPECTRA_WIFI_PASSWORD      "YOUR_WIFI_PASSWORD"
#define SPECTRA_WS_URI             "ws://192.168.1.100:8765"
#define SPECTRA_WS_TIMEOUT_MS      5000

/* ── Streaming ──────────────────────────────────────────────────── */
#define SPECTRA_STREAM_TIMEOUT_MS  10000  /* max streaming duration */
#define SPECTRA_STREAM_CHUNK_SAMP  1600   /* send 100ms of audio per chunk */

/* ── Timing ─────────────────────────────────────────────────────── */
#define SPECTRA_WIFI_CONNECT_TIMEOUT_MS  10000

#endif /* SPECTRA_CONFIG_H_ */
