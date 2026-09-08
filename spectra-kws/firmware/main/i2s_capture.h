/**
 * @file i2s_capture.h
 * @brief I2S DMA audio capture from INMP441 microphone.
 *
 * Runs as a FreeRTOS task. I2S DMA writes samples into a ring buffer
 * without CPU intervention — "zero-copy" capture.
 */

#ifndef I2S_CAPTURE_H_
#define I2S_CAPTURE_H_

#include <stdint.h>
#include <stddef.h>

/**
 * Initialise I2S peripheral and DMA for 16 kHz, 16-bit, mono capture.
 * Configures INMP441 wiring: SCK, WS, SD pins.
 */
void i2s_capture_init(void);

/**
 * Start the I2S capture task (runs continuously, fills ring buffer).
 *
 * @param task_priority  FreeRTOS task priority
 * @param task_core      CPU core to pin the task to
 */
void i2s_capture_start(int task_priority, int task_core);

/**
 * Read the most recent N samples from the ring buffer.
 * Copies samples into the provided buffer (caller-allocated).
 *
 * @param dest       destination buffer (int16_t*)
 * @param n_samples  number of samples to read
 * @return           number of samples actually copied
 */
size_t i2s_capture_read(int16_t *dest, size_t n_samples);

/**
 * Read the full ring buffer content (for flushing after wake-word trigger).
 *
 * @param dest       destination buffer (int16_t*), must be at least
 *                   SPECTRA_RING_BUF_SAMPLES in size
 * @return           number of samples copied
 */
size_t i2s_capture_flush(int16_t *dest);

/**
 * Get the total number of samples captured since init (for timestamps).
 */
uint64_t i2s_capture_total_samples(void);

#endif /* I2S_CAPTURE_H_ */
