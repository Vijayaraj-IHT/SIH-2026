/**
 * @file main.c
 * @brief Spectra KWS — Main application entry point.
 *
 * System startup sequence:
 *   1. NVS, clock, logging
 *   2. I2S capture (INMP441 → ring buffer)
 *   3. MFCC tables (pre-computed)
 *   4. KWS engine (TFLite Micro model load)
 *   5. Trigger logic (posterior smoothing)
 *   6. Wi-Fi + WebSocket client
 *
 * Main loop (runs every SPECTRA_INFER_EVERY_MS):
 *   - Read last 1s of audio from ring buffer
 *   - Extract MFCC features
 *   - Run DS-CNN inference
 *   - Feed posteriors to trigger logic
 *   - If triggered → flush ring buffer → stream audio → receive transcript
 *
 * Latency budget:
 *   I2S DMA:    0 µs CPU (continuous)
 *   MFCC:       ~3 ms
 *   DS-CNN:     ~15 ms
 *   Trigger:    ~0.1 ms
 *   Wi-Fi:      ~50 ms (ring buffer flush + WS open)
 *   Total:      ~70 ms device-side (before ASR server)
 */

#include <stdio.h>
#include <string.h>

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_system.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "nvs_flash.h"

#include "spectra_config.h"
#include "i2s_capture.h"
#include "mfcc.h"
#include "kws_engine.h"
#include "trigger_logic.h"
#include "ws_stream.h"

static const char *TAG = "spectra";

/* ── Feature buffer ─────────────────────────────────────────────── */

static float s_features[SPECTRA_N_FRAMES * SPECTRA_N_FEATURES];
static int16_t s_audio_buf[SPECTRA_SAMPLE_RATE];  /* 1 second of audio */
static float s_posteriors[SPECTRA_N_CLASSES];
static int16_t s_ring_flush[SPECTRA_RING_BUF_SAMPLES];

/* ── Timing stats ───────────────────────────────────────────────── */

static int64_t s_last_trigger_time = 0;
static uint32_t s_trigger_count = 0;

/* ── Main Application Task ──────────────────────────────────────── */

static void spectra_task(void *arg)
{
    ESP_LOGI(TAG, "╔══════════════════════════════════════╗");
    ESP_LOGI(TAG, "║   SPECTRA — Listening for wake word  ║");
    ESP_LOGI(TAG, "╚══════════════════════════════════════╝");

    TickType_t xLastWakeTime = xTaskGetTickCount();
    const TickType_t xFrequency = pdMS_TO_TICKS(SPECTRA_INFER_EVERY_MS);

    while (1) {
        int64_t t_loop_start = esp_timer_get_time();

        /* 1. Read last 1 second of audio from ring buffer */
        i2s_capture_read(s_audio_buf, SPECTRA_SAMPLE_RATE);

        /* 2. Extract MFCC features */
        int64_t t_mfcc_start = esp_timer_get_time();
        mfcc_extract(s_audio_buf, s_features);
        int64_t t_mfcc_end = esp_timer_get_time();

        /* 3. Run DS-CNN inference */
        int64_t t_kws_start = esp_timer_get_time();
        int ret = kws_engine_invoke(s_features, s_posteriors);
        int64_t t_kws_end = esp_timer_get_time();

        if (ret != 0) {
            ESP_LOGE(TAG, "KWS inference failed!");
            vTaskDelayUntil(&xLastWakeTime, xFrequency);
            continue;
        }

        /* 4. Feed to trigger logic */
        bool triggered = trigger_logic_feed(s_posteriors);

        int64_t t_loop_end = esp_timer_get_time();
        int loop_ms = (int)((t_loop_end - t_loop_start) / 1000);
        int mfcc_ms = (int)((t_mfcc_end - t_mfcc_start) / 1000);
        int kws_ms = (int)((t_kws_end - t_kws_start) / 1000);

        /* 5. Periodic status print */
        static int print_counter = 0;
        if (++print_counter >= 50) {  /* every ~10 seconds at 200ms interval */
            print_counter = 0;
            ESP_LOGI(TAG, "Listening... "
                     "[spectra=%.3f unknown=%.3f silence=%.3f] "
                     "[smooth=%.3f hits=%d] "
                     "[mfcc=%dms kws=%dms total=%dms] "
                     "[triggers=%lu]",
                     s_posteriors[SPECTRA_CLASS_SPECTRA],
                     s_posteriors[SPECTRA_CLASS_UNKNOWN],
                     s_posteriors[SPECTRA_CLASS_SILENCE],
                     trigger_logic_smoothed_score(),
                     trigger_logic_consecutive_hits(),
                     mfcc_ms, kws_ms, loop_ms,
                     (unsigned long)s_trigger_count);
        }

        /* 6. Handle trigger */
        if (triggered) {
            s_trigger_count++;
            s_last_trigger_time = t_loop_end;

            int64_t t_trigger = esp_timer_get_time();
            int trigger_latency_ms = (int)((t_trigger - t_loop_start) / 1000);

            ESP_LOGI(TAG, "🎯 Wake-word detected! (detection latency: %d ms)", trigger_latency_ms);

            /* Flush ring buffer */
            size_t flushed = i2s_capture_flush(s_ring_flush);
            ESP_LOGI(TAG, "  Ring buffer flushed: %zu samples (%.0f ms)",
                     flushed, (float)flushed / SPECTRA_SAMPLE_RATE * 1000);

            /* Stream audio to ASR server */
            ws_stream_audio(s_ring_flush, flushed);

            /* Reset trigger state */
            trigger_logic_reset();

            ESP_LOGI(TAG, "╔══════════════════════════════════════╗");
            ESP_LOGI(TAG, "║   SPECTRA — Listening for wake word  ║");
            ESP_LOGI(TAG, "╚══════════════════════════════════════╝");
        }

        /* Wait for next inference cycle */
        vTaskDelayUntil(&xLastWakeTime, xFrequency);
    }
}

/* ── Application Entry Point ────────────────────────────────────── */

void app_main(void)
{
    ESP_LOGI(TAG, "╔══════════════════════════════════════════════╗");
    ESP_LOGI(TAG, "║  SPECTRA — Low-Latency Voice Activator      ║");
    ESP_LOGI(TAG, "║  SIH 2026 · PS 26172                        ║");
    ESP_LOGI(TAG, "║  Target: XIAO ESP32-C5 + INMP441            ║");
    ESP_LOGI(TAG, "╚══════════════════════════════════════════════╝");

    /* ── NVS (required by Wi-Fi) ────────────────────────────────── */
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);

    /* ── Stage 1: I2S Audio Capture ─────────────────────────────── */
    ESP_LOGI(TAG, "\n▸ Stage 1: I2S Audio Capture");
    i2s_capture_init();
    i2s_capture_start(5, 0);  /* priority 5, core 0 */

    /* ── Stage 2: MFCC Feature Extraction ───────────────────────── */
    ESP_LOGI(TAG, "\n▸ Stage 2: MFCC Feature Extraction");
    mfcc_init();

    /* ── Stage 3: KWS Engine (TFLite Micro) ─────────────────────── */
    ESP_LOGI(TAG, "\n▸ Stage 3: KWS Engine");
    if (kws_engine_init() != 0) {
        ESP_LOGE(TAG, "FATAL: KWS engine init failed!");
        return;
    }

    /* ── Stage 4: Trigger Logic ─────────────────────────────────── */
    ESP_LOGI(TAG, "\n▸ Stage 4: Trigger Logic");
    trigger_logic_init();

    /* ── Stage 5: Wi-Fi + WebSocket ─────────────────────────────── */
    ESP_LOGI(TAG, "\n▸ Stage 5: Wi-Fi + WebSocket");
    if (ws_stream_init() != 0) {
        ESP_LOGW(TAG, "⚠ Wi-Fi/WS init failed — will retry on trigger");
        /* Non-fatal: device still listens locally */
    }

    /* ── Stage 6: Start main loop ───────────────────────────────── */
    ESP_LOGI(TAG, "\n▸ Stage 6: Starting main inference loop");
    ESP_LOGI(TAG, "  Inference interval: %d ms", SPECTRA_INFER_EVERY_MS);
    ESP_LOGI(TAG, "  Trigger threshold:  θ = %.2f", SPECTRA_TRIGGER_THRESHOLD);
    ESP_LOGI(TAG, "  Smooth windows:    %d", SPECTRA_SMOOTH_WINDOWS);
    ESP_LOGI(TAG, "  Consecutive hits:  %d", SPECTRA_CONSECUTIVE_HITS);

    xTaskCreatePinnedToCore(
        spectra_task,
        "spectra_main",
        16384,       /* large stack for MFCC + inference */
        NULL,
        6,           /* high priority */
        NULL,
        1            /* core 1 (separate from I2S capture) */
    );
}
