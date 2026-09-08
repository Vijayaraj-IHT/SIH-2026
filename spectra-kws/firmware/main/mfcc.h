/**
 * @file mfcc.h
 * @brief C implementation of MFCC feature extraction for ESP32-C5.
 *
 * This MUST produce bit-identical output to the Python features.py
 * given the same input audio. The constants are in spectra_config.h.
 *
 * Pipeline (per frame):
 *   Pre-emphasis → Framing → Hamming → FFT → Mel filterbank → log → DCT
 *
 * Output: (49, 10) float32 matrix, per-utterance normalised.
 */

#ifndef MFCC_H_
#define MFCC_H_

#include <stdint.h>
#include "spectra_config.h"

/**
 * Initialise MFCC state (pre-compute window, filterbank, DCT matrix).
 * Call once at startup.
 */
void mfcc_init(void);

/**
 * Extract MFCC features from 1 second of 16-bit PCM audio.
 *
 * @param pcm_samples   input: 16000 × int16_t samples
 * @param features      output: (49 × 10) float32 array
 *                      caller must provide at least 49*10 floats
 */
void mfcc_extract(const int16_t *pcm_samples, float *features);

/**
 * Get pointer to the MFCC scratch buffer (for debugging).
 */
float *mfcc_debug_buffer(void);

#endif /* MFCC_H_ */
