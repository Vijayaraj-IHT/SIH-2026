# ESP32 → AGNI-ASR Handover Protocol (v1)

Exact wire contract between the edge voice activator and the cloud gateway.
The PC simulator that speaks this protocol: `cloud/scripts/client_handover.py`.

## Transports (either is accepted by the stack)

| Transport | Endpoint / Topic | When to use |
|---|---|---|
| HTTPS REST | `POST {GATEWAY}/v1/transcribe` | simplest firmware path, stateless |
| MQTT v3.1.1 | publish `agni/{device_id}/audio`, subscribe `agni/{device_id}/intent` | low RAM devices, async dashboard feeding |

## Payload (JSON, UTF-8)

```json
{
  "device_id": "esp32-node-07",
  "audio_format": "pcm16",          // raw little-endian signed int16, mono, 16000 Hz
  "audio_b64": "<base64 of 2.0 s = 64000 bytes PCM = 85332 base64 chars>",
  "keyword": "jump",                // enrolled keyword that fired (informational)
  "prototype": [ -0.042, 0.181, ... ],   // 32 floats — the SAME unit vector stored
                                         // in NVS by scripts/enroll_keyword.py (optional)
  "expect_intent": true
}
```

* Audio slice = ring-buffer pre-roll (wake utterance, ~1.0 s) + command audio (~1.0 s).
  The co-verifier embeds only the **first 1.0 s** (`verifier.wake_span_end_s`) so the
  command speech never contaminates the wake-word embedding.
* `audio_format` options: `pcm16` (raw, default), **`flac`** (~50 % payload, lossless,
  one-liner client-side — recommended), `wav` (testing), `opus` (24 kbps, needs opuslib).
  No server-side resampling needed at 16 kHz.

## Response (200)

```json
{
  "transcript": "abort payload",
  "language": "en",
  "intent": {"type": "command", "action": "abort", "subsystem": "payload",
             "raw": "abort payload", "wake_keyword": "jump"},
  "verification": {"verified": true, "cosine": 0.91, "threshold": 0.7},
  "timing": {"asr_ms": 132, "total_ms": 148, "audio_s": 2.0}
}
```

Intent contract seen by firmware:

| `intent.type` | Meaning | Firmware action |
|---|---|---|
| `command` | grammar matched; fields `action/subsystem/channel/mode/voltage` present | execute + ack beep |
| `freeform` | valid speech, not in command grammar | forward to dashboard display |
| `blocked`  | co-verifier veto (wake-word mismatch on server) | reject, log, stay armed |
| `null`     | silence / noise / low confidence | reject |

## Auth & hardening

* REST: header `X-API-Key: <AGNI_API_TOKEN>` (set via env on the gateway; never commit it).
* MQTT dev broker is anonymous on LAN. Finals profile: listener 8883 + `cafile/certfile/
  keyfile` + `password_file`, payloads unchanged. Firewall 8000/8883 to the demo network.
* Reframing for judges: the identical `docker compose` runs on-prem ("ground-station mode"),
  so the wire contract works with *no internet* — cloud is the training site, not a dependency.

## Firmware pseudo-flow (into `voice_activator_esp32_wroom.ino`)

```
on ACTIVATION:
    WiFi.begin(...)                       // or use always-on link
    snap  = ring_buffer.snapshot(2.0 s)   // pre-roll + post-trigger audio
    proto = nvs_read_32f("prototype")
    json  = build_payload(device_id, snap, proto, keyword)
    http.POST(gateway + "/v1/transcribe", json, headers=X-API-Key)
    on intent.type == command -> execute GPIO/actuator + beep(2)
    on blocked/null           -> beep(1, low)
```
