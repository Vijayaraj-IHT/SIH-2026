/**
 * @file trigger_logic.c
 * @brief Posterior smoothing and wake-word trigger detection.
 *
 * Strategy:
 *   1. Keep a circular buffer of the last SPECTRA_SMOOTH_WINDOWS "spectra"
 *      posteriors from the KWS engine.
 *   2. Compute a smoothed score (exponential moving average).
 *   3. Count consecutive windows where smoothed_score > threshold.
 *   4. Fire trigger when consecutive count reaches SPECTRA_CONSECUTIVE_HITS.
 *   5. Enter cooldown to prevent re-triggers.
 *
 * This turns a noisy per-frame classifier into a reliable binary switch
 * with very few false alarms.
 */

#include "trigger_logic.h"
#include "spectra_config.h"

#include "esp_log.h"
#include <string.h>

static const char *TAG = "trigger";

/* ── State ──────────────────────────────────────────────────────── */

static float s_posterior_buf[SPECTRA_SMOOTH_WINDOWS];
static int s_buf_idx = 0;
static int s_buf_count = 0;           /* how many windows we've seen */
static int s_consecutive_hits = 0;
static bool s_cooldown = false;
static int64_t s_cooldown_start = 0;

/* Cooldown: 2 seconds after trigger before accepting new triggers */
#define COOLDOWN_MS 2000

/* ── Public API ─────────────────────────────────────────────────── */

void trigger_logic_init(void)
{
    memset(s_posterior_buf, 0, sizeof(s_posterior_buf));
    s_buf_idx = 0;
    s_buf_count = 0;
    s_consecutive_hits = 0;
    s_cooldown = false;
    ESP_LOGI(TAG, "Trigger logic initialised (θ=%.2f, smooth=%d, hits=%d, cooldown=%dms)",
             SPECTRA_TRIGGER_THRESHOLD, SPECTRA_SMOOTH_WINDOWS,
             SPECTRA_CONSECUTIVE_HITS, COOLDOWN_MS);
}

bool trigger_logic_feed(const float *posteriors)
{
    float spectra_score = posteriors[SPECTRA_CLASS_SPECTRA];

    /* Store in circular buffer */
    s_posterior_buf[s_buf_idx] = spectra_score;
    s_buf_idx = (s_buf_idx + 1) % SPECTRA_SMOOTH_WINDOWS;
    if (s_buf_count < SPECTRA_SMOOTH_WINDOWS) {
        s_buf_count++;
    }

    /* Don't trigger until we have enough windows */
    if (s_buf_count < SPECTRA_SMOOTH_WINDOWS) {
        return false;
    }

    /* Check cooldown */
    if (s_cooldown) {
        int64_t now_ms = esp_timer_get_time() / 1000;
        if (now_ms - s_cooldown_start < COOLDOWN_MS) {
            return false;
        }
        s_cooldown = false;
        s_consecutive_hits = 0;
        ESP_LOGI(TAG, "Cooldown expired");
    }

    /* Compute smoothed score (exponential moving average) */
    float smoothed = 0.0f;
    float alpha = 0.6f;  /* EMA weight for most recent */
    float weight = 1.0f;
    float total_weight = 0.0f;

    for (int i = 0; i < SPECTRA_SMOOTH_WINDOWS; i++) {
        int idx = (s_buf_idx + SPECTRA_SMOOTH_WINDOWS - 1 - i) % SPECTRA_SMOOTH_WINDOWS;
        smoothed += s_posterior_buf[idx] * weight;
        total_weight += weight;
        weight *= alpha;
    }
    smoothed /= total_weight;

    /* Check threshold */
    if (smoothed >= SPECTRA_TRIGGER_THRESHOLD) {
        s_consecutive_hits++;
    } else {
        s_consecutive_hits = 0;
    }

    /* Fire trigger */
    if (s_consecutive_hits >= SPECTRA_CONSECUTIVE_HITS) {
        ESP_LOGI(TAG, "🎯 WAKE-WORD DETECTED! (smoothed=%.3f, hits=%d)",
                 smoothed, s_consecutive_hits);

        s_cooldown = true;
        s_cooldown_start = esp_timer_get_time() / 1000;
        s_consecutive_hits = 0;

        return true;
    }

    return false;
}

void trigger_logic_reset(void)
{
    s_consecutive_hits = 0;
    s_cooldown = false;
    memset(s_posterior_buf, 0, sizeof(s_posterior_buf));
    s_buf_idx = 0;
    s_buf_count = 0;
}

float trigger_logic_smoothed_score(void)
{
    if (s_buf_count == 0) return 0.0f;

    float smoothed = 0.0f;
    float alpha = 0.6f;
    float weight = 1.0f;
    float total_weight = 0.0f;

    for (int i = 0; i < s_buf_count; i++) {
        int idx = (s_buf_idx + s_buf_count - 1 - i) % SPECTRA_SMOOTH_WINDOWS;
        smoothed += s_posterior_buf[idx] * weight;
        total_weight += weight;
        weight *= alpha;
    }
    return smoothed / total_weight;
}

int trigger_logic_consecutive_hits(void)
{
    return s_consecutive_hits;
}
