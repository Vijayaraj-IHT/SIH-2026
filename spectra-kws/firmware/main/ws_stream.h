/**
 * @file ws_stream.h
 * @brief WebSocket audio streaming to cloud ASR server.
 *
 * After a wake-word trigger:
 *   1. Flush the ring buffer (pre-trigger audio)
 *   2. Open WebSocket to ASR server
 *   3. Stream live audio until end-of-speech or timeout
 *   4. Receive and display transcript
 *   5. Close connection and return to listening
 */

#ifndef WS_STREAM_H_
#define WS_STREAM_H_

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

/**
 * Initialise the WebSocket client and Wi-Fi connection.
 * Call once at startup. Connects to SPECTRA_WIFI_SSID.
 *
 * @return 0 on success, -1 on failure
 */
int ws_stream_init(void);

/**
 * Stream audio to the ASR server after wake-word detection.
 *
 * @param pre_trigger_audio  ring buffer content (500 ms)
 * @param pre_trigger_len    number of samples in the ring buffer
 *
 * This function:
 *   - Opens a WebSocket connection (if not already open)
 *   - Sends a "start" command
 *   - Flushes pre_trigger_audio first
 *   - Reads live audio from i2s_capture and streams it
 *   - Waits for end-of-speech or timeout
 *   - Sends "end" command
 *   - Receives and prints the transcript
 *   - Returns
 */
void ws_stream_audio(const int16_t *pre_trigger_audio, size_t pre_trigger_len);

/**
 * Check if Wi-Fi is connected.
 */
bool ws_stream_wifi_connected(void);

/**
 * Get round-trip time estimate (ms) from last stream.
 */
int ws_stream_last_rtt_ms(void);

#endif /* WS_STREAM_H_ */
