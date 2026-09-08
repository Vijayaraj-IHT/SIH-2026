/**
 * @file ws_stream.c
 * @brief WebSocket audio streaming to cloud ASR server.
 *
 * Protocol (matches server/asr_server.py):
 *   Client → Server:
 *     Binary frames: raw 16-bit PCM, 16 kHz, mono (little-endian)
 *     Text frames:   JSON {"cmd": "start"|"end"|"cancel"}
 *   Server → Client:
 *     Text frames:   JSON {"type": "partial"|"final"|"error", ...}
 *
 * Flow after wake-word:
 *   1. Open WS, send {"cmd": "start"}
 *   2. Send ring buffer (500 ms pre-trigger audio)
 *   3. Send live audio in chunks until end-of-speech or timeout
 *   4. Send {"cmd": "end"}
 *   5. Receive transcript
 *   6. Close or reuse connection
 */

#include "ws_stream.h"
#include "spectra_config.h"
#include "i2s_capture.h"

#include "esp_wifi.h"
#include "esp_event.h"
#include "esp_netif.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "esp_websocket_client.h"
#include "nvs_flash.h"

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/event_groups.h"

#include <string.h>
#include <stdio.h>

static const char *TAG = "ws_stream";

/* ── Wi-Fi event group ──────────────────────────────────────────── */

static EventGroupHandle_t s_wifi_event_group;
#define WIFI_CONNECTED_BIT BIT0
#define WIFI_FAIL_BIT      BIT1

static int s_wifi_retry_count = 0;
#define WIFI_MAX_RETRY 5

static bool s_wifi_connected = false;

/* ── WebSocket client ───────────────────────────────────────────── */

static esp_websocket_client_handle_t s_ws_client = NULL;
static bool s_ws_connected = false;

/* ── Transcript buffer ──────────────────────────────────────────── */

#define TRANSCRIPT_BUF_SIZE 1024
static char s_transcript[TRANSCRIPT_BUF_SIZE];
static int s_last_rtt_ms = 0;

/* ── Wi-Fi event handler ────────────────────────────────────────── */

static void wifi_event_handler(void *arg, esp_event_base_t event_base,
                               int32_t event_id, void *event_data)
{
    if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_START) {
        esp_wifi_connect();
    } else if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_DISCONNECTED) {
        s_wifi_connected = false;
        if (s_wifi_retry_count < WIFI_MAX_RETRY) {
            esp_wifi_connect();
            s_wifi_retry_count++;
            ESP_LOGW(TAG, "Wi-Fi reconnecting... (attempt %d/%d)", s_wifi_retry_count, WIFI_MAX_RETRY);
        } else {
            xEventGroupSetBits(s_wifi_event_group, WIFI_FAIL_BIT);
            ESP_LOGE(TAG, "Wi-Fi connection failed after %d attempts", WIFI_MAX_RETRY);
        }
    } else if (event_base == IP_EVENT && event_id == IP_EVENT_STA_GOT_IP) {
        ip_event_got_ip_t *event = (ip_event_got_ip_t *)event_data;
        ESP_LOGI(TAG, "Wi-Fi connected! IP: " IPSTR, IP2STR(&event->ip_info.ip));
        s_wifi_retry_count = 0;
        s_wifi_connected = true;
        xEventGroupSetBits(s_wifi_event_group, WIFI_CONNECTED_BIT);
    }
}

/* ── WebSocket event handler ────────────────────────────────────── */

static void ws_event_handler(void *arg, esp_event_base_t event_base,
                             int32_t event_id, void *event_data)
{
    esp_websocket_event_data_t *data = (esp_websocket_event_data_t *)event_data;

    switch (event_id) {
    case WEBSOCKET_EVENT_CONNECTED:
        ESP_LOGI(TAG, "WebSocket connected");
        s_ws_connected = true;
        break;

    case WEBSOCKET_EVENT_DISCONNECTED:
        ESP_LOGI(TAG, "WebSocket disconnected");
        s_ws_connected = false;
        break;

    case WEBSOCKET_EVENT_DATA:
        if (data->op_code == 0x01) {  /* text frame */
            /* Parse server response */
            char *msg = data->data_ptr;
            int msg_len = data->data_len;

            if (msg_len > 0 && msg_len < TRANSCRIPT_BUF_SIZE) {
                memcpy(s_transcript, msg, msg_len);
                s_transcript[msg_len] = '\0';

                /* Log based on type */
                if (strstr(s_transcript, "\"final\"")) {
                    ESP_LOGI(TAG, "📝 Final: %s", s_transcript);
                } else if (strstr(s_transcript, "\"partial\"")) {
                    ESP_LOGI(TAG, "  Partial: %s", s_transcript);
                } else if (strstr(s_transcript, "\"error\"")) {
                    ESP_LOGE(TAG, "Error: %s", s_transcript);
                }
            }
        }
        break;

    case WEBSOCKET_EVENT_ERROR:
        ESP_LOGE(TAG, "WebSocket error");
        break;

    default:
        break;
    }
}

/* ── Wi-Fi Init ─────────────────────────────────────────────────── */

static int wifi_init(void)
{
    ESP_LOGI(TAG, "Initialising Wi-Fi...");

    s_wifi_event_group = xEventGroupCreate();

    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());
    esp_netif_create_default_wifi_sta();

    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&cfg));

    /* Register event handlers */
    ESP_ERROR_CHECK(esp_event_handler_instance_register(
        WIFI_EVENT, ESP_EVENT_ANY_ID, &wifi_event_handler, NULL, NULL));
    ESP_ERROR_CHECK(esp_event_handler_instance_register(
        IP_EVENT, IP_EVENT_STA_GOT_IP, &wifi_event_handler, NULL, NULL));

    /* Configure station */
    wifi_config_t wifi_config = {
        .sta = {
            .ssid = SPECTRA_WIFI_SSID,
            .password = SPECTRA_WIFI_PASSWORD,
            .threshold.authmode = WIFI_AUTH_WPA2_PSK,
        },
    };

    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &wifi_config));
    ESP_ERROR_CHECK(esp_wifi_start());

    /* Wait for connection */
    EventBits_t bits = xEventGroupWaitBits(
        s_wifi_event_group,
        WIFI_CONNECTED_BIT | WIFI_FAIL_BIT,
        pdFALSE, pdFALSE,
        pdMS_TO_TICKS(SPECTRA_WIFI_CONNECT_TIMEOUT_MS)
    );

    if (bits & WIFI_CONNECTED_BIT) {
        ESP_LOGI(TAG, "Wi-Fi connected ✓");
        return 0;
    } else {
        ESP_LOGE(TAG, "Wi-Fi connection failed ✗");
        return -1;
    }
}

/* ── WebSocket Init ─────────────────────────────────────────────── */

static int ws_init(void)
{
    ESP_LOGI(TAG, "Initialising WebSocket client: %s", SPECTRA_WS_URI);

    esp_websocket_client_config_t ws_cfg = {
        .uri = SPECTRA_WS_URI,
        .buffer_size = 4096,
        .reconnect_timeout_ms = SPECTRA_WS_TIMEOUT_MS,
        .network_timeout_ms = SPECTRA_WS_TIMEOUT_MS,
    };

    s_ws_client = esp_websocket_client_init(&ws_cfg);
    esp_websocket_register_events(s_ws_client, WEBSOCKET_EVENT_ANY, ws_event_handler, NULL);

    esp_err_t err = esp_websocket_client_start(s_ws_client);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "WebSocket start failed: %s", esp_err_to_name(err));
        return -1;
    }

    /* Wait for connection */
    int wait_ms = 0;
    while (!s_ws_connected && wait_ms < SPECTRA_WS_TIMEOUT_MS) {
        vTaskDelay(pdMS_TO_TICKS(100));
        wait_ms += 100;
    }

    if (!s_ws_connected) {
        ESP_LOGE(TAG, "WebSocket connection timeout");
        return -1;
    }

    ESP_LOGI(TAG, "WebSocket connected ✓");
    return 0;
}

/* ── Public API ─────────────────────────────────────────────────── */

int ws_stream_init(void)
{
    int ret = wifi_init();
    if (ret != 0) return ret;

    ret = ws_init();
    return ret;
}

void ws_stream_audio(const int16_t *pre_trigger_audio, size_t pre_trigger_len)
{
    if (!s_ws_connected || !s_ws_client) {
        ESP_LOGE(TAG, "WebSocket not connected, cannot stream");
        return;
    }

    int64_t t_start = esp_timer_get_time();
    s_transcript[0] = '\0';

    ESP_LOGI(TAG, "═══ Streaming started ═══");

    /* 1. Send "start" command */
    esp_websocket_client_send_text(s_ws_client, "{\"cmd\":\"start\"}", 15, pdMS_TO_TICKS(1000));
    vTaskDelay(pdMS_TO_TICKS(50));  /* brief pause for server to prepare */

    /* 2. Flush pre-trigger ring buffer (500 ms of audio) */
    ESP_LOGI(TAG, "Sending %zu pre-trigger samples (%.0f ms)...",
             pre_trigger_len, (float)pre_trigger_len / SPECTRA_SAMPLE_RATE * 1000);

    size_t bytes_per_chunk = SPECTRA_STREAM_CHUNK_SAMP * sizeof(int16_t);
    size_t offset = 0;
    while (offset < pre_trigger_len) {
        size_t chunk_samples = pre_trigger_len - offset;
        if (chunk_samples > SPECTRA_STREAM_CHUNK_SAMP) {
            chunk_samples = SPECTRA_STREAM_CHUNK_SAMP;
        }
        esp_websocket_client_send_bin(
            s_ws_client,
            (const char *)(pre_trigger_audio + offset),
            chunk_samples * sizeof(int16_t),
            pdMS_TO_TICKS(1000)
        );
        offset += chunk_samples;
    }

    /* 3. Stream live audio until timeout */
    int64_t stream_start = esp_timer_get_time();
    int64_t timeout_us = (int64_t)SPECTRA_STREAM_TIMEOUT_MS * 1000;
    int16_t live_buf[SPECTRA_STREAM_CHUNK_SAMP];

    while ((esp_timer_get_time() - stream_start) < timeout_us) {
        size_t read = i2s_capture_read(live_buf, SPECTRA_STREAM_CHUNK_SAMP);
        if (read > 0) {
            esp_websocket_client_send_bin(
                s_ws_client,
                (const char *)live_buf,
                read * sizeof(int16_t),
                pdMS_TO_TICKS(1000)
            );
        }
        vTaskDelay(pdMS_TO_TICKS(SPECTRA_STREAM_CHUNK_SAMP * 1000 / SPECTRA_SAMPLE_RATE));
    }

    /* 4. Send "end" command */
    esp_websocket_client_send_text(s_ws_client, "{\"cmd\":\"end\"}", 13, pdMS_TO_TICKS(1000));

    /* 5. Wait for final transcript */
    int wait_ms = 0;
    while (!strstr(s_transcript, "\"final\"") && wait_ms < 5000) {
        vTaskDelay(pdMS_TO_TICKS(100));
        wait_ms += 100;
    }

    int64_t t_end = esp_timer_get_time();
    s_last_rtt_ms = (int)((t_end - t_start) / 1000);

    ESP_LOGI(TAG, "═══ Streaming complete ═══");
    ESP_LOGI(TAG, "  Total time: %d ms", s_last_rtt_ms);
    ESP_LOGI(TAG, "  Transcript: %s", s_transcript);
}

bool ws_stream_wifi_connected(void)
{
    return s_wifi_connected;
}

int ws_stream_last_rtt_ms(void)
{
    return s_last_rtt_ms;
}
