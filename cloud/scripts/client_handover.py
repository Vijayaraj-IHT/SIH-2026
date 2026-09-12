#!/usr/bin/env python3
"""PC-side handover client — byte-for-byte simulator of the ESP32 payload.

Use it to test the gateway without hardware (or as `src/streaming/cloud_handover.py`
reference implementation for the live-mic Python activator).

  python client_handover.py --wav demo.wav --server http://localhost:8000
  python client_handover.py --wav demo.wav --keyword jump --prototype random
  python client_handover.py --wav demo.wav --mode mqtt --mqtt-host localhost
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import time

import numpy as np


def load_wav_pcm16(path: str, target_sr: int = 16000) -> bytes:
    import soundfile as sf
    data, sr = sf.read(path, dtype="float32", always_2d=True)
    mono = data.mean(axis=1)
    if sr != target_sr:  # same linear resample as server-side convenience path
        x = np.linspace(0, mono.size - 1, int(mono.size * target_sr / sr))
        mono = np.interp(x, np.arange(mono.size), mono).astype(np.float32)
    return (np.clip(mono, -1, 1) * 32767).astype("<i2").tobytes()


def encode_audio(wav_path: str, fmt: str) -> bytes:
    pcm = load_wav_pcm16(wav_path)
    if fmt == "pcm16":
        return pcm
    import numpy as _np
    x = _np.frombuffer(pcm, dtype="<i2").astype(_np.float32) / 32768.0
    if fmt == "flac":
        import io as _io
        import soundfile as _sf
        buf = _io.BytesIO()
        _sf.write(buf, x, 16000, format="FLAC", subtype="PCM_16")
        return buf.getvalue()
    if fmt == "opus":
        import opuslib
        enc = opuslib.Encoder(16000, 1, opuslib.APPLICATION_AUDIO)
        enc.bitrate = 24000
        xi = (x * 32767).astype("<i2")
        return b"".join(enc.encode(xi[i:i + 960].tobytes(), 960)
                        for i in range(0, len(xi), 960))
    raise ValueError(fmt)


def make_payload(wav_path: str, keyword: str | None, prototype: str | None,
                 fmt: str = "pcm16") -> dict:
    audio_b = encode_audio(wav_path, fmt)
    print(f"[transport] {fmt}: {len(audio_b)} bytes "
          f"({100 * len(audio_b) / (len(load_wav_pcm16(wav_path)) or 1):.0f}% of pcm16)")
    proto = None
    if prototype == "random":  # dev stub; real flow ships the ESP32 NVS vector
        rng = np.random.default_rng(42)
        v = rng.standard_normal(32).astype(np.float32)
        proto = (v / np.linalg.norm(v)).round(6).tolist()
    elif prototype and prototype != "none":
        proto = json.load(open(prototype))
    return {"device_id": "pc-sim-01", "audio_b64": base64.b64encode(audio_b).decode(),
            "audio_format": fmt, "keyword": keyword, "prototype": proto}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wav", required=True)
    ap.add_argument("--server", default="http://localhost:8000")
    ap.add_argument("--token", default="dev-token")
    ap.add_argument("--keyword", default=None)
    ap.add_argument("--prototype", default="none", help="'random' | path to json | none")
    ap.add_argument("--mode", choices=["http", "mqtt"], default="http")
    ap.add_argument("--fmt", choices=["pcm16", "flac", "opus"], default="pcm16")
    ap.add_argument("--mqtt-host", default="localhost")
    ap.add_argument("--mqtt-port", type=int, default=1883)
    a = ap.parse_args()

    p = make_payload(a.wav, a.keyword, a.prototype, a.fmt)
    t0 = time.perf_counter()

    if a.mode == "http":
        import urllib.request
        req = urllib.request.Request(
            f"{a.server}/v1/transcribe", data=json.dumps(p).encode(),
            headers={"Content-Type": "application/json", "X-API-Key": a.token})
        with urllib.request.urlopen(req) as r:
            out = json.loads(r.read())
    else:
        import paho.mqtt.client as mqtt
        import paho.mqtt.subscribe as sub
        cli = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id="pc-sim-pub")
        cli.connect(a.mqtt_host, a.mqtt_port, 30)
        cli.publish(f"agni/{p['device_id']}/audio", json.dumps(p), qos=1)
        cli.disconnect()
        out = json.loads(sub.simple(f"agni/{p['device_id']}/intent",
                                    hostname=a.mqtt_host, port=a.mqtt_port,
                                    msg_count=1).payload)

    print(json.dumps(out, indent=2))
    print(f"\nwall-clock: {int((time.perf_counter()-t0)*1000)} ms "
          f"(server-reported: {out.get('timing', {}).get('total_ms')} ms)")


if __name__ == "__main__":
    main()
