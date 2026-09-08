"""
Spectra ASR Server — WebSocket + faster-whisper

Receives 16-bit PCM audio from the ESP32-C5 over WebSocket,
runs faster-whisper (Whisper-class ASR), and streams back
transcript tokens.

Protocol:
  Client → Server:
    Binary frame: raw 16-bit PCM, 16 kHz, mono (little-endian)
    Text frame:   JSON control messages
      {"cmd": "start"}  — begin new utterance
      {"cmd": "end"}    — utterance complete, finalise
      {"cmd": "cancel"} — discard current utterance

  Server → Client:
    Text frame: JSON transcript messages
      {"type": "partial", "text": "..."}   — partial result
      {"type": "final", "text": "..."}     — final result
      {"type": "error", "message": "..."}  — error

Usage:
  python asr_server.py --host 0.0.0.0 --port 8765
"""

import argparse
import asyncio
import json
import struct
import time
from collections import deque
from typing import Optional

import numpy as np
import websockets

# faster-whisper import (lazy, so --help works without the model downloaded)
_whisper_model = None


def get_whisper_model(model_size: str = "base", device: str = "auto"):
    """Lazy-load the faster-whisper model."""
    global _whisper_model
    if _whisper_model is None:
        from faster_whisper import WhisperModel
        print(f"Loading faster-whisper model '{model_size}'...")
        _whisper_model = WhisperModel(model_size, device=device, compute_type="int8")
        print(f"  Model loaded successfully.")
    return _whisper_model


class Session:
    """Manages audio accumulation and transcription for one client."""

    def __init__(self, model_size: str = "base"):
        self.model_size = model_size
        self.audio_buffer = bytearray()
        self.is_active = False
        self.start_time: Optional[float] = None

    def start(self):
        """Begin a new utterance."""
        self.audio_buffer = bytearray()
        self.is_active = True
        self.start_time = time.time()
        print(f"  [Session] Utterance started")

    def append_audio(self, pcm_bytes: bytes):
        """Append raw PCM audio to the buffer."""
        if self.is_active:
            self.audio_buffer.extend(pcm_bytes)

    async def finalize(self, websocket) -> Optional[str]:
        """
        Finalize the utterance: run ASR and send results.

        Returns the final transcript text.
        """
        if not self.is_active:
            return None

        self.is_active = False
        elapsed = time.time() - self.start_time if self.start_time else 0
        audio_duration = len(self.audio_buffer) / (16000 * 2)  # 16-bit = 2 bytes/sample

        print(f"  [Session] Utterance finalized: {len(self.audio_buffer)} bytes, "
              f"{audio_duration:.2f}s audio, {elapsed:.2f}s elapsed")

        if len(self.audio_buffer) < 3200:  # < 100ms of audio
            await websocket.send(json.dumps({
                "type": "error", "message": "Audio too short"
            }))
            return ""

        # Convert PCM bytes to float32
        pcm_samples = np.frombuffer(self.audio_buffer, dtype=np.int16)
        audio_float = pcm_samples.astype(np.float32) / 32768.0

        # Run ASR
        try:
            t0 = time.time()
            model = get_whisper_model(self.model_size)
            segments, info = model.transcribe(
                audio_float,
                language="en",
                beam_size=5,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=300),
            )
            asr_time = time.time() - t0

            full_text = ""
            for segment in segments:
                text = segment.text.strip()
                if text:
                    full_text += text + " "
                    # Send partial result
                    await websocket.send(json.dumps({
                        "type": "partial",
                        "text": text,
                    }))

            full_text = full_text.strip()

            # Send final result
            await websocket.send(json.dumps({
                "type": "final",
                "text": full_text,
                "asr_time_ms": int(asr_time * 1000),
                "audio_duration_s": round(audio_duration, 2),
            }))

            print(f"  [Session] Transcript: '{full_text}' (ASR: {asr_time*1000:.0f}ms)")
            return full_text

        except Exception as e:
            error_msg = f"ASR error: {str(e)}"
            print(f"  [Session] {error_msg}")
            await websocket.send(json.dumps({
                "type": "error", "message": error_msg,
            }))
            return None

    def cancel(self):
        """Cancel the current utterance."""
        self.is_active = False
        self.audio_buffer = bytearray()
        print(f"  [Session] Utterance cancelled")


async def handle_client(websocket, model_size: str):
    """Handle a single WebSocket client connection."""
    client_id = id(websocket)
    print(f"[Client {client_id}] Connected from {websocket.remote_address}")

    session = Session(model_size)

    try:
        async for message in websocket:
            if isinstance(message, bytes):
                # Binary frame = PCM audio data
                session.append_audio(message)

            elif isinstance(message, str):
                # Text frame = JSON control message
                try:
                    cmd = json.loads(message)
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({
                        "type": "error", "message": "Invalid JSON"
                    }))
                    continue

                cmd_type = cmd.get("cmd")

                if cmd_type == "start":
                    session.start()
                    await websocket.send(json.dumps({
                        "type": "status", "state": "listening"
                    }))

                elif cmd_type == "end":
                    await session.finalize(websocket)

                elif cmd_type == "cancel":
                    session.cancel()
                    await websocket.send(json.dumps({
                        "type": "status", "state": "idle"
                    }))

                elif cmd_type == "ping":
                    await websocket.send(json.dumps({"type": "pong"}))

                else:
                    await websocket.send(json.dumps({
                        "type": "error", "message": f"Unknown command: {cmd_type}"
                    }))

    except websockets.exceptions.ConnectionClosed:
        print(f"[Client {client_id}] Disconnected")
    except Exception as e:
        print(f"[Client {client_id}] Error: {e}")
    finally:
        session.cancel()


async def main():
    parser = argparse.ArgumentParser(description="Spectra ASR WebSocket Server")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Bind host")
    parser.add_argument("--port", type=int, default=8765, help="Bind port")
    parser.add_argument("--model", type=str, default="base",
                        help="Whisper model size (tiny/base/small/medium)")
    parser.add_argument("--device", type=str, default="auto",
                        help="Device (cpu/cuda/auto)")
    args = parser.parse_args()

    # Pre-load model
    get_whisper_model(args.model, args.device)

    print(f"\nSpectra ASR Server")
    print(f"  WebSocket: ws://{args.host}:{args.port}")
    print(f"  Model:     faster-whisper ({args.model})")
    print(f"  Protocol:  PCM 16-bit, 16 kHz, mono")
    print(f"\nWaiting for connections...\n")

    async with websockets.serve(
        lambda ws: handle_client(ws, args.model),
        args.host,
        args.port,
        max_size=10 * 1024 * 1024,  # 10 MB max message
        ping_interval=20,
        ping_timeout=20,
    ):
        await asyncio.Future()  # Run forever


if __name__ == "__main__":
    try:
        import uvloop
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    except ImportError:
        pass
    asyncio.run(main())
