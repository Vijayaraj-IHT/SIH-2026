/**
 * @file mfcc.c
 * @brief C MFCC feature extraction — must match Python features.py exactly.
 *
 * Pipeline:
 *   1. Pre-emphasis (α = 0.97)
 *   2. Framing: 25ms window, 10ms hop → 98 frames for 1s @ 16kHz
 *   3. Hamming window
 *   4. 256-point FFT → power spectrum
 *   5. 40-band Mel filterbank (60–7800 Hz)
 *   6. Log(energy) per band
 *   7. DCT-II → keep first 13 coefficients
 *   8. Select first 10 features per frame
 *   9. Centre-crop to 49 frames
 *  10. Per-utterance normalisation (zero mean, unit variance)
 *
 * All constants must match spectra_config.h exactly.
 */

#include "mfcc.h"
#include "spectra_config.h"

#include <math.h>
#include <string.h>
#include "esp_log.h"
#include "esp_dsp.h"   /* ESP-IDF DSP library for FFT */

static const char *TAG = "mfcc";

/* ── Pre-computed tables (allocated once at init) ───────────────── */

/* Hamming window: SPECTRA_FRAME_LENGTH_SAMP floats */
static float s_hamming[SPECTRA_FRAME_LENGTH_SAMP];

/* Mel filterbank: N_MELS × (FFT_SIZE/2 + 1) */
#define FFT_BINS (SPECTRA_FFT_SIZE / 2 + 1)
static float s_fbank[SPECTRA_N_MELS][FFT_BINS];

/* DCT-II matrix: N_MFCC × N_MELS (orthonormal) */
static float s_dct[SPECTRA_N_MFCC][SPECTRA_N_MELS];

/* Scratch buffers */
static float s_frame[SPECTRA_FRAME_LENGTH_SAMP];
static float s_fft_input[SPECTRA_FFT_SIZE];
static float s_fft_output[SPECTRA_FFT_SIZE];  /* complex interleaved */
static float s_power[FFT_BINS];
static float s_mel_energy[SPECTRA_N_MELS];
static float s_log_mel[SPECTRA_N_MELS];
static float s_mfcc[SPECTRA_TOTAL_FRAMES][SPECTRA_N_MFCC];

/* Audio as float (for pre-emphasis) */
static float s_audio_float[SPECTRA_SAMPLE_RATE];

/* ── Helper: Hz ↔ Mel ───────────────────────────────────────────── */

static inline float hz_to_mel(float hz)
{
    return 2595.0f * log10f(1.0f + hz / 700.0f);
}

static inline float mel_to_hz(float mel)
{
    return 700.0f * (powf(10.0f, mel / 2595.0f) - 1.0f);
}

/* ── Helper: DCT-II (orthonormal) ───────────────────────────────── */

static void init_dct(void)
{
    for (int k = 0; k < SPECTRA_N_MFCC; k++) {
        for (int n = 0; n < SPECTRA_N_MELS; n++) {
            if (k == 0) {
                s_dct[k][n] = sqrtf(1.0f / SPECTRA_N_MELS);
            } else {
                s_dct[k][n] = sqrtf(2.0f / SPECTRA_N_MELS)
                              * cosf(M_PI * k * (2.0f * n + 1.0f) / (2.0f * SPECTRA_N_MELS));
            }
        }
    }
}

/* ── Helper: Mel filterbank ─────────────────────────────────────── */

static void init_fbank(void)
{
    memset(s_fbank, 0, sizeof(s_fbank));

    float low_mel = hz_to_mel(SPECTRA_MEL_LOW_HZ);
    float high_mel = hz_to_mel(SPECTRA_MEL_HIGH_HZ);

    /* Centre frequencies in Hz for N_MELS + 2 points */
    float mel_points[SPECTRA_N_MELS + 2];
    for (int i = 0; i < SPECTRA_N_MELS + 2; i++) {
        mel_points[i] = mel_to_hz(low_mel + (high_mel - low_mel) * i / (SPECTRA_N_MELS + 1));
    }

    /* Convert to FFT bin indices */
    int bins[SPECTRA_N_MELS + 2];
    for (int i = 0; i < SPECTRA_N_MELS + 2; i++) {
        bins[i] = (int)floorf((SPECTRA_FFT_SIZE + 1) * mel_points[i] / SPECTRA_SAMPLE_RATE);
        if (bins[i] >= FFT_BINS) bins[i] = FFT_BINS - 1;
    }

    /* Triangular filters */
    for (int m = 0; m < SPECTRA_N_MELS; m++) {
        int left = bins[m];
        int centre = bins[m + 1];
        int right = bins[m + 2];

        for (int k = left; k < centre; k++) {
            if (centre != left) {
                s_fbank[m][k] = (float)(k - left) / (float)(centre - left);
            }
        }
        for (int k = centre; k <= right; k++) {
            if (right != centre) {
                s_fbank[m][k] = (float)(right - k) / (float)(right - centre);
            }
        }
    }
}

/* ── Helper: Hamming window ─────────────────────────────────────── */

static void init_hamming(void)
{
    for (int i = 0; i < SPECTRA_FRAME_LENGTH_SAMP; i++) {
        s_hamming[i] = 0.54f - 0.46f * cosf(2.0f * M_PI * i / (SPECTRA_FRAME_LENGTH_SAMP - 1));
    }
}

/* ── Init ───────────────────────────────────────────────────────── */

void mfcc_init(void)
{
    ESP_LOGI(TAG, "Initialising MFCC tables...");
    ESP_LOGI(TAG, "  Frame: %d samples (%d ms), Hop: %d samples (%d ms)",
             SPECTRA_FRAME_LENGTH_SAMP, SPECTRA_FRAME_LENGTH_MS,
             SPECTRA_FRAME_SHIFT_SAMP, SPECTRA_FRAME_SHIFT_MS);
    ESP_LOGI(TAG, "  FFT: %d bins, Mel bands: %d, MFCCs: %d, Features: %d",
             FFT_BINS, SPECTRA_N_MELS, SPECTRA_N_MFCC, SPECTRA_N_FEATURES);
    ESP_LOGI(TAG, "  Total frames: %d, Output frames: %d",
             SPECTRA_TOTAL_FRAMES, SPECTRA_N_FRAMES);

    init_hamming();
    init_fbank();
    init_dct();

    /* Initialize ESP-DSP FFT */
    dsps_fft2r_init_fc32(NULL, SPECTRA_FFT_SIZE);

    ESP_LOGI(TAG, "MFCC tables initialised ✓");
}

/* ── Extract MFCCs ──────────────────────────────────────────────── */

void mfcc_extract(const int16_t *pcm_samples, float *features)
{
    /*
     * features must point to SPECTRA_N_FRAMES × SPECTRA_N_FEATURES floats.
     * i.e. 49 × 10 = 490 floats.
     */

    /* 1. Convert int16 → float and apply pre-emphasis */
    s_audio_float[0] = (float)pcm_samples[0] / 32768.0f;
    for (int i = 1; i < SPECTRA_SAMPLE_RATE; i++) {
        float sample = (float)pcm_samples[i] / 32768.0f;
        s_audio_float[i] = sample - 0.97f * ((float)pcm_samples[i - 1] / 32768.0f);
    }

    /* 2–6. Process each frame */
    for (int f = 0; f < SPECTRA_TOTAL_FRAMES; f++) {
        int offset = f * SPECTRA_FRAME_SHIFT_SAMP;

        /* 3. Hamming window */
        for (int i = 0; i < SPECTRA_FRAME_LENGTH_SAMP; i++) {
            s_frame[i] = s_audio_float[offset + i] * s_hamming[i];
        }

        /* 4. FFT (zero-pad to FFT_SIZE) */
        memset(s_fft_input, 0, sizeof(s_fft_input));
        memcpy(s_fft_input, s_frame, SPECTRA_FRAME_LENGTH_SAMP * sizeof(float));

        /* ESP-DSP in-place FFT (real → complex interleaved) */
        dsps_fft2r_fc32(s_fft_input, SPECTRA_FFT_SIZE);
        /* Convert to split complex for power calculation */
        dsps_bit_rev_fc32(s_fft_input, SPECTRA_FFT_SIZE);

        /* Power spectrum: |X[k]|^2 */
        for (int k = 0; k < FFT_BINS; k++) {
            float re = s_fft_input[2 * k];
            float im = s_fft_input[2 * k + 1];
            s_power[k] = re * re + im * im;
        }

        /* 5. Mel filterbank */
        memset(s_mel_energy, 0, sizeof(s_mel_energy));
        for (int m = 0; m < SPECTRA_N_MELS; m++) {
            for (int k = 0; k < FFT_BINS; k++) {
                s_mel_energy[m] += s_power[k] * s_fbank[m][k];
            }
            /* Avoid log(0) */
            if (s_mel_energy[m] < 1e-10f) s_mel_energy[m] = 1e-10f;
        }

        /* 6. Log energy */
        for (int m = 0; m < SPECTRA_N_MELS; m++) {
            s_log_mel[m] = logf(s_mel_energy[m]);
        }

        /* 7. DCT-II → MFCCs */
        for (int c = 0; c < SPECTRA_N_MFCC; c++) {
            float sum = 0.0f;
            for (int m = 0; m < SPECTRA_N_MELS; m++) {
                sum += s_log_mel[m] * s_dct[c][m];
            }
            s_mfcc[f][c] = sum;
        }
    }

    /* 8–9. Centre-crop to SPECTRA_N_FRAMES frames, select first N_FEATURES */
    int start_frame = (SPECTRA_TOTAL_FRAMES - SPECTRA_N_FRAMES) / 2;

    /* 10. Per-utterance normalisation — compute mean and std first */
    float mean[SPECTRA_N_FEATURES];
    float std[SPECTRA_N_FEATURES];
    memset(mean, 0, sizeof(mean));
    memset(std, 0, sizeof(std));

    for (int f = 0; f < SPECTRA_N_FRAMES; f++) {
        int src_f = start_frame + f;
        for (int c = 0; c < SPECTRA_N_FEATURES; c++) {
            mean[c] += s_mfcc[src_f][c];
        }
    }
    for (int c = 0; c < SPECTRA_N_FEATURES; c++) {
        mean[c] /= SPECTRA_N_FRAMES;
    }

    for (int f = 0; f < SPECTRA_N_FRAMES; f++) {
        int src_f = start_frame + f;
        for (int c = 0; c < SPECTRA_N_FEATURES; c++) {
            float diff = s_mfcc[src_f][c] - mean[c];
            std[c] += diff * diff;
        }
    }
    for (int c = 0; c < SPECTRA_N_FEATURES; c++) {
        std[c] = sqrtf(std[c] / SPECTRA_N_FRAMES) + 1e-8f;
    }

    /* Write normalised features to output */
    for (int f = 0; f < SPECTRA_N_FRAMES; f++) {
        int src_f = start_frame + f;
        for (int c = 0; c < SPECTRA_N_FEATURES; c++) {
            features[f * SPECTRA_N_FEATURES + c] =
                (s_mfcc[src_f][c] - mean[c]) / std[c];
        }
    }
}

float *mfcc_debug_buffer(void)
{
    return &s_mfcc[0][0];
}
