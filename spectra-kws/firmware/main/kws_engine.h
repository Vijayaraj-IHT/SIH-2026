/**
 * @file kws_engine.h
 * @brief TensorFlow Lite Micro inference wrapper for DS-CNN-S.
 *
 * Wraps TFLite Micro to run the quantised INT8 model on the ESP32-C5.
 * Model is embedded as a C byte array in spectra_model.h.
 */

#ifndef KWS_ENGINE_H_
#define KWS_ENGINE_H_

#include <stdint.h>

/**
 * Initialise the TFLite Micro interpreter.
 * Allocates tensors, loads the model from flash.
 * Call once at startup.
 *
 * @return 0 on success, -1 on failure
 */
int kws_engine_init(void);

/**
 * Run inference on a single MFCC feature matrix.
 *
 * @param features   input: (49 × 10) float32 MFCC features
 * @param output     output: (3) float32 probabilities [spectra, unknown, silence]
 *                   These are softmax-normalised posteriors.
 * @return           0 on success, -1 on failure
 */
int kws_engine_invoke(const float *features, float *output);

/**
 * Run inference and return only the predicted class index.
 *
 * @param features   input: (49 × 10) float32 MFCC features
 * @return           class index (0=spectra, 1=unknown, 2=silence), or -1 on error
 */
int kws_engine_predict(const float *features);

/**
 * Get the last inference time in microseconds.
 */
int64_t kws_engine_last_inference_us(void);

/**
 * Get the arena (working memory) usage in bytes.
 */
size_t kws_engine_arena_usage(void);

#endif /* KWS_ENGINE_H_ */
