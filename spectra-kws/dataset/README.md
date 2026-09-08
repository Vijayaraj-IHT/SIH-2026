# Spectra Dataset — Collection & Organisation Guide

## Directory Structure

```
dataset/
├── positives/          "Spectra" recordings (wake word)
├── negatives/          Other words (Google Speech Commands)
├── confusion/          Similar-sounding words
└── background/         Ambient noise recordings
```

---

## 1. Positives (`positives/`)

Recordings of the wake word "Spectra".

### Recording Matrix (4 conditions)

| Condition | Speed | Distance | Filename pattern |
|---|---|---|---|
| Slow + Near | Deliberate, clear | 30–50 cm | `spectra_slow_near_*.wav` |
| Slow + Far | Deliberate, clear | 2–3 m | `spectra_slow_far_*.wav` |
| Fast + Near | Natural, quick | 30–50 cm | `spectra_fast_near_*.wav` |
| Fast + Far | Natural, quick | 2–3 m | `spectra_fast_far_*.wav` |

### Recording Specifications

- **Format**: WAV, 16-bit PCM, mono
- **Sample rate**: 16 kHz (resample if recorded at different rate)
- **Duration**: Trim to 1 second (pad silence if shorter)
- **Speakers**: Minimum 20 speakers, balanced gender (M/F/Other)
- **Environments**: Record at least 30% of clips through the actual INMP441 microphone
- **Minimum per condition**: 50 clips per condition (200 total minimum, 500+ recommended)

### Metadata

Include a `metadata.csv` with columns:
```csv
filename,speaker_id,gender,condition,environment,notes
spectra_slow_near_001.wav,S01,M,slow_near,office,clear pronunciation
```

### Google Form Collection

Use the Google Form with these fields:
1. **Audio upload** — Record "Spectra" (the wake word)
2. **Speaking speed** — Slow / Normal / Fast
3. **Distance** — Near (< 1m) / Far (> 1m)
4. **Gender** — M / F / Other / Prefer not to say
5. **Environment** — Quiet room / Noisy room / Outdoors
6. **Device** — Phone mic / INMP441 board / Other

---

## 2. Negatives (`negatives/`)

Use the [Google Speech Commands v2](https://www.tensorflow.org/datasets/catalog/speech_commands) dataset.

### Download

```bash
# Option A: via Hugging Face datasets
python -c "
import datasets, shutil, os
ds = datasets.load_dataset('speech_commands', 'v0.02', split='train')
os.makedirs('negatives', exist_ok=True)
# Extract and convert to 16kHz WAV
"

# Option B: direct download
wget http://download.tensorflow.org/data/speech_commands_v0.02.tar.gz
tar -xzf speech_commands_v0.02.tar.gz -C negatives/
```

### Required Words (35)

```
yes, no, up, down, left, right, on, off, stop, go,
zero, one, two, three, four, five, six, seven, eight, nine,
bed, bird, cat, dog, happy, house, marvin, sheila, tree, wow,
backward, forward, follow, learn, visual
```

These cover a range of phonemes and are well-established as negative classes for KWS.

### Processing

All negatives should be:
- Converted to 16 kHz, 16-bit WAV, mono
- Trimmed/padded to exactly 1 second
- Renamed: `{word}_{speaker}_{id}.wav`

---

## 3. Confusion Words (`confusion/`)

Words phonetically similar to "Spectra" — the model must reject these.

### Target Words

| Word | Why it's confusing |
|---|---|
| spectrum | Near-homophone, shares "spectr-" onset |
| expect | Shares "spect" cluster |
| extra | Similar vowel pattern |
| sector | Shares consonant-vowel flow |
| spectral | Adjective form — different ending |
| spectacular | Shares onset but longer |
| inspector | Shares "spect" + schwa |
| suspect | Reversed syllable structure |

### Recording

- Use the same recording setup as positives
- Minimum 20 clips per word
- Multiple speakers, mixed conditions

---

## 4. Background Noise (`background/`)

Ambient noise recordings for augmentation.

### Sources

- **Office** — keyboard typing, AC hum, distant conversation
- **Street** — traffic, wind, distant voices
- **Home** — TV, kitchen sounds, fan noise
- **Hall** — echo-heavy room (for demo venue matching)

### Specifications

- 30-second continuous recordings (WAV, 16-bit, 16 kHz, mono)
- Minimum 5 different environments
- These are mixed into positives at random SNR (5–20 dB) during training

---

## 5. Data Pipeline Summary

```
Raw recordings
    │
    ├── Trim to 1s, resample to 16kHz
    ├── Remove silence / bad recordings
    ├── Balance classes (oversample positives if needed)
    │
    ▼
    dataset/
        positives/  → label 0 (spectra)
        negatives/  → label 1 (unknown)
        confusion/  → label 1 (unknown)
        background/ → augmentation only (label 2 = silence)
```

## 6. Expected Dataset Sizes

| Class | Minimum | Recommended | Source |
|---|---|---|---|
| spectra (positives) | 200 | 500+ | Google Form + direct recording |
| unknown (negatives) | 3,000 | 10,000+ | Google Speech Commands |
| unknown (confusion) | 160 | 500+ | Direct recording |
| background noise | 5 × 30s | 20 × 30s | Direct recording |

## 7. Domain Matching

> **Critical**: Record at least 30% of positives through the actual INMP441 on the ESP32-C5 board.

This ensures the training data frequency response matches the deployment audio. Without this, the model may learn spectral artifacts of the recording device that don't exist in deployment.
