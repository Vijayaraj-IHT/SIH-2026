/**
 * @file i2s_capture.c
 * @brief I2S DMA audio capture from INMP441 microphone.
 *
 * I2S DMA continuously writes 16 kHz, 16-bit samples into a circular
 * buffer. The CPU is not involved in the copy — this is the "zero-cost"
 * capture stage from the architecture diagram.
 *
 * The ring buffer holds the last SPECTRA_RING_BUF_MS milliseconds
 * of audio, which is flushed to the WebSocket stream when the
 * wake-word is detected (so the first syllable after "Spectra"
 * is never lost).
 */

#include "i2s_capture.h"
#include "spectra_config.h"

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/i2s_std.h"
#include "esp_log.h"
#include <string.h>

static const char *TAG = "i2s_capture";

/* ── Ring Buffer ────────────────────────────────────────────────── */

static int16_t s_ring_buf[SPECTRA_RING_BUF_SAMPLES];
static volatile size_t s_write_idx = 0;       /* next write position */
static volatile uint64_t s_total_samples = 0;  /* total samples captured */

/* ── I2S Handle ─────────────────────────────────────────────────── */

static i2s_chan_handle_t s_rx_handle = NULL;
static TaskHandle_t s_capture_task = NULL;

/* ── DMA Buffer ─────────────────────────────────────────────────── */

/* DMA read buffer — 1024 samples per read (~64ms at 16kHz) */
#define DMA_BUF_SAMPLES 1024
static int16_t s_dma_buf[DMA_BUF_SAMPLES];

/* ── Ring buffer write ──────────────────────────────────────────── */

static void ring_buf_write(const int16_t *data, size_t n)
{
    for (size_t i = 0; i < n; i++) {
        s_ring_buf[s_write_idx] = data[i];
        s_write_idx = (s_write_idx + 1) % SPECTRA_RING_BUF_SAMPLES;
    }
    s_total_samples += n;
}

/* ── Capture Task ───────────────────────────────────────────────── */

static void capture_task(void *arg)
{
    size_t bytes_read = 0;
    ESP_LOGI(TAG, "Capture task started (I2S DMA → ring buffer)");

    while (1) {
        /* Read from I2S DMA — blocks until data available */
        esp_err_t err = i2s_channel_read(
            s_rx_handle,
            s_dma_buf,
            sizeof(s_dma_buf),
            &bytes_read,
            portMAX_DELAY
        );

        if (err != ESP_OK) {
            ESP_LOGE(TAG, "I2S read error: %s", esp_err_to_name(err));
            vTaskDelay(pdMS_TO_TICKS(10));
            continue;
        }

        size_t samples_read = bytes_read / sizeof(int16_t);
        ring_buf_write(s_dma_buf, samples_read);
    }
}

/* ── Public API ─────────────────────────────────────────────────── */

void i2s_capture_init(void)
{
    ESP_LOGI(TAG, "Initialising I2S capture...");
    ESP_LOGI(TAG, "  Sample rate: %d Hz, Bits: %d", SPECTRA_SAMPLE_RATE, SPECTRA_I2S_BITS);
    ESP_LOGI(TAG, "  SCK=%d, WS=%d, SD=%d", SPECTRA_I2S_SCK_PIN, SPECTRA_I2S_WS_PIN, SPECTRA_I2S_SD_PIN);
    ESP_LOGI(TAG, "  Ring buffer: %d samples (%d ms)", SPECTRA_RING_BUF_SAMPLES, SPECTRA_RING_BUF_MS);

    /* Configure I2S channel */
    i2s_chan_config_t chan_cfg = I2S_CHANNEL_DEFAULT_CONFIG(I2S_NUM_0, I2S_ROLE_MASTER);
    chan_cfg.auto_clear = true;

    ESP_ERROR_CHECK(i2s_new_channel(&chan_cfg, NULL, &s_rx_handle));

    /* Configure I2S standard mode for INMP441 */
    i2s_std_config_t std_cfg = {
        .clk_cfg = I2S_STD_CLK_DEFAULT_CONFIG(SPECTRA_SAMPLE_RATE),
        .slot_cfg = I2S_STD_PHILIPS_SLOT_DEFAULT_CONFIG(
            I2S_DATA_BIT_WIDTH_16BIT,
            I2S_SLOT_MODE_MONO
        ),
        .gpio_cfg = {
            .mclk = I2S_GPIO_UNUSED,
            .bclk = (gpio_num_t)SPECTRA_I2S_SCK_PIN,
            .ws   = (gpio_num_t)SPECTRA_I2S_WS_PIN,
            .dout = I2S_GPIO_UNUSED,
            .din  = (gpio_num_t)SPECTRA_I2S_SD_PIN,
            .invert_flags = {
                .mclk_inv = false,
                .bclk_inv = false,
                .ws_inv   = false,
            },
        },
    };

    ESP_ERROR_CHECK(i2s_channel_init_std_mode(s_rx_handle, &std_cfg));
    ESP_ERROR_CHECK(i2s_channel_enable(s_rx_handle));

    /* Clear ring buffer */
    memset(s_ring_buf, 0, sizeof(s_ring_buf));
    s_write_idx = 0;
    s_total_samples = 0;

    ESP_LOGI(TAG, "I2S capture initialised ✓");
}

void i2s_capture_start(int task_priority, int task_core)
{
    xTaskCreatePinnedToCore(
        capture_task,
        "i2s_capture",
        4096,            /* stack size */
        NULL,
        task_priority,
        &s_capture_task,
        task_core
    );
    ESP_LOGI(TAG, "Capture task started on core %d (priority %d)", task_core, task_priority);
}

size_t i2s_capture_read(int16_t *dest, size_t n_samples)
{
    /* Read the most recent n_samples from the ring buffer */
    if (n_samples > SPECTRA_RING_BUF_SAMPLES) {
        n_samples = SPECTRA_RING_BUF_SAMPLES;
    }

    size_t read_start = (s_write_idx + SPECTRA_RING_BUF_SAMPLES - n_samples)
                        % SPECTRA_RING_BUF_SAMPLES;

    for (size_t i = 0; i < n_samples; i++) {
        dest[i] = s_ring_buf[(read_start + i) % SPECTRA_RING_BUF_SAMPLES];
    }

    return n_samples;
}

size_t i2s_capture_flush(int16_t *dest)
{
    return i2s_capture_read(dest, SPECTRA_RING_BUF_SAMPLES);
}

uint64_t i2s_capture_total_samples(void)
{
    return s_total_samples;
}
