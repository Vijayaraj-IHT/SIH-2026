"""FastAPI entrypoint — AGNI-ASR gateway.

Endpoints:
  GET  /healthz          liveness + model info
  POST /v1/transcribe    ESP32 handover (JSON b64 or multipart) -> transcript + intent
  POST /v1/enroll        dashboard-side prototype inspection (dev aid)
  WS   /ws/asr           chunked PCM16 stream -> final transcript (dev + dashboard)

Run:  uvicorn serving.api_gateway:app --host 0.0.0.0 --port 8000
Docs: http://<host>:8000/docs (Swagger UI)
"""
from __future__ import annotations

import base64
import json
import logging
import time

from pathlib import Path

import numpy as np
from fastapi import (Depends, FastAPI, File, Form, Header, HTTPException,
                     UploadFile, WebSocket, WebSocketDisconnect)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from .audio_utils import b64_to_float, clamp_duration, load_any, rms_db
from .config import load_config
from .pipeline import AgniPipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
log = logging.getLogger("agni.gateway")

CFG = load_config()
PIPE = AgniPipeline(CFG)
app = FastAPI(title="AGNI-ASR — SIH-26172 Cloud Speech Gateway", version="0.1.0")

# CORS: the judge dashboard may be served from file:// or another port in dev.
# Finals hardening: pin allow_origins to the dashboard host.
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"],
                   allow_headers=["*"])

_DASHBOARD = Path(__file__).resolve().parent.parent / "dashboard" / "index.html"


@app.get("/", include_in_schema=False)
@app.get("/dashboard", include_in_schema=False)
def dashboard():
    if _DASHBOARD.exists():
        return FileResponse(str(_DASHBOARD))
    return {"hint": "dashboard file missing at " + str(_DASHBOARD)}

# optional in-process MQTT bridge
_BRIDGE = None
if CFG["mqtt"]["enabled"]:
    from .mqtt_bridge import MqttBridge
    _BRIDGE = MqttBridge(CFG, PIPE)
    _BRIDGE.start()

# optional command model (fast path) — only imported when enabled, so the
# zero-training gateway never pays the torch cost it doesn't need
_COMMAND = None
if CFG.get("command_model", {}).get("enabled"):
    from .command_worker import CommandWorker
    _COMMAND = CommandWorker(CFG["command_model"]["ckpt_path"],
                             CFG["intent"]["grammar_path"],
                             use_grammar=CFG["command_model"].get("grammar_decode", True))
    log.info("command model: trained=%s", _COMMAND.trained)


def _partial_decode_fn():
    if _COMMAND is not None:
        return lambda buf: _COMMAND.decode(buf)["text"]
    return None  # command model off -> partials report progress only


# --------------------------------------------------------------------- models
class HandoverPayload(BaseModel):
    """Exact schema the ESP32 firmware sends (see docs/HANDOVER_PROTOCOL.md)."""
    device_id: str = "esp32-dev-01"
    audio_b64: str = Field(description="base64 little-endian PCM16, mono, 16 kHz")
    audio_format: str = "pcm16"                      # pcm16 | wav (opus: Session 3)
    keyword: str | None = None                       # enrolled keyword that fired
    prototype: list[float] | None = None             # 32 floats, S^31 unit vector
    expect_intent: bool = True


# ---------------------------------------------------------------------- auth
def require_token(x_api_key: str = Header(default="")):
    if x_api_key != CFG["server"]["api_token"]:
        raise HTTPException(status_code=401, detail="invalid X-API-Key")


# ------------------------------------------------------------------ endpoints
@app.get("/healthz")
def healthz():
    return {"status": "ok", "model": PIPE.asr.model_size, "device": PIPE.asr.device,
            "model_load_ms": PIPE.asr.load_ms,
            "verifier": "ready" if PIPE.verifier.available
                        else f"degraded ({PIPE.verifier.reason})",
            "mqtt": "enabled" if _BRIDGE else "disabled"}


@app.post("/v1/transcribe", dependencies=[Depends(require_token)])
async def transcribe_json(p: HandoverPayload):
    if len(p.audio_b64) * 3 // 4 > CFG["limits"]["max_upload_bytes"]:
        raise HTTPException(413, "payload exceeds max_upload_bytes")
    try:
        audio = load_any(base64.b64decode(p.audio_b64), p.audio_format)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(400, f"audio decode failed: {e}")
    audio = clamp_duration(audio, CFG["limits"]["max_payload_s"])
    log.info("handover %s kw=%s %.2fs rms=%.1fdB", p.device_id, p.keyword,
             len(audio) / 16000, rms_db(audio))
    return await run_in_threadpool(PIPE.process, audio, p.prototype, p.keyword)


@app.post("/v1/transcribe/upload", dependencies=[Depends(require_token)])
async def transcribe_upload(file: UploadFile = File(...), meta: str = Form(default="{}")):
    """Convenience endpoint for PC testing: multipart WAV upload."""
    meta_d = json.loads(meta) if meta else {}
    raw = await file.read()
    audio = clamp_duration(load_any(raw, "wav"), CFG["limits"]["max_payload_s"])
    return await run_in_threadpool(PIPE.process, audio,
                                   meta_d.get("prototype"), meta_d.get("keyword"))


@app.websocket("/ws/asr")
async def ws_asr(ws: WebSocket):
    """Streaming path: 1 config frame, then binary PCM16/FLAC chunks.

    - With command model enabled: real PARTIAL transcripts every ~400 ms
      (grammar-constrained), final event on VAD silence, then the full
      whisper-grade result JSON (with verifier + intent) on {"finalize": true}.
    - Without it: partial progress events every chunk, final = full result.
    """
    from .partial_decoder import PartialDecoder
    await ws.accept()
    # browsers cannot set WS headers -> accept ?token= as an equivalent credential
    token = ws.headers.get("x-api-key", "") or ws.query_params.get("token", "")
    if token != CFG["server"]["api_token"]:
        await ws.close(code=4401); return
    p = CFG.get("partials", {})
    dec = PartialDecoder(decode_fn=_partial_decode_fn(),
                         partial_every_s=p.get("partial_every_s", 0.4),
                         silence_ms=p.get("silence_end_ms", 600),
                         max_utt_s=p.get("max_utt_s", 8.0))
    buf: list[np.ndarray] = []
    meta: dict = {}
    try:
        while True:
            msg = await ws.receive()
            if msg.get("text"):
                d = json.loads(msg["text"])
                if d.get("finalize"):
                    fin = dec.finalize()
                    audio = np.concatenate(buf) if buf else np.zeros(0, np.float32)
                    buf.clear()
                    audio = clamp_duration(audio, CFG["limits"]["max_payload_s"])
                    res = await run_in_threadpool(PIPE.process, audio,
                                                  meta.get("prototype"), meta.get("keyword"))
                    if _COMMAND is not None:
                        res["command"] = await run_in_threadpool(_COMMAND.decode, audio)
                    res["stream"] = fin
                    await ws.send_json({"type": "result", **res})
                else:
                    meta.update(d)
                    await ws.send_json({"type": "ack",
                                        "command_model": _COMMAND is not None})
            elif msg.get("bytes"):
                chunk = np.frombuffer(msg["bytes"], dtype="<i2").astype(np.float32) / 32768.0
                buf.append(chunk)
                for ev in dec.push(chunk):
                    if ev["type"] == "final":
                        ev["note"] = ("auto end-of-speech; send {'finalize': true} "
                                      "for the full verifier+intent result")
                    await ws.send_json(ev)
            elif msg.get("type") == "websocket.disconnect":
                break
    except (WebSocketDisconnect, RuntimeError):
        pass  # clean or abrupt client hang-up — both are normal session ends


@app.exception_handler(Exception)
async def unhandled(_r, e):  # keep JSON contract even on 500s (judge-proofing)
    log.exception("unhandled")
    return JSONResponse(status_code=500, content={"error": str(e)})
