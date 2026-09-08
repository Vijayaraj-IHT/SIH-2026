/**
 * @file trigger_logic.h
 * @brief Posterior smoothing and wake-word trigger detection.
 *
 * Implements the trigger logic from the architecture:
 *   - Maintains a sliding window of SPECTRA_SMOOTH_WINDOWS posteriors
 *   - Fires when "spectra" posterior > θ for SPECTRA_CONSECUTIVE_HITS
 *     consecutive windows
 *   - After firing, enters a cooldown period to prevent re-triggers
 */

#ifndef TRIGGER_LOGIC_H_
#define TRIGGER_LOGIC_H_

#include <stdbool.h>
#include "spectra_config.h"

/**
 * Initialise the trigger logic state.
 * Call once at startup.
 */
void trigger_logic_init(void);

/**
 * Feed a new set of class probabilities from the KWS engine.
 *
 * @param posteriors  float[SPECTRA_N_CLASSES] softmax probabilities
 *                    [spectra, unknown, silence]
 *
 * @return true if the wake-word was detected (trigger fired)
 */
bool trigger_logic_feed(const float *posteriors);

/**
 * Reset the trigger state (after streaming completes).
 */
void trigger_logic_reset(void);

/**
 * Get the smoothed "spectra" posterior (for debugging / serial display).
 */
float trigger_logic_smoothed_score(void);

/**
 * Get the number of consecutive hits (for debugging).
 */
int trigger_logic_consecutive_hits(void);

#endif /* TRIGGER_LOGIC_H_ */
