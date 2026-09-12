"""MQTT bridge — ESP32 nodes publish handover payloads; intents come back.

Topics (cloud.yaml -> mqtt.*):
  sub: agni/+/audio          payload: HandoverPayload JSON (same schema as REST)
  pub: agni/{device}/intent  payload: {"intent": {...}, "transcript": "...", ...}

Run standalone:   python -m serving.mqtt_bridge
Or auto-started by api_gateway when mqtt.enabled=true (in-process).
"""
from __future__ import annotations

import json
import logging
import threading

import paho.mqtt.client as mqtt

from .audio_utils import b64_to_float, clamp_duration
from .pipeline import AgniPipeline  # shared ASR+verifier+router core

log = logging.getLogger("agni.mqtt")


class MqttBridge:
    def __init__(self, cfg: dict, pipeline: AgniPipeline):
        self.cfg, self.pipe = cfg["mqtt"], pipeline
        self.tcp = cfg["limits"]
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1,
                                  client_id="agni-asr-bridge")
        if self.cfg.get("username"):
            self.client.username_pw_set(self.cfg["username"], self.cfg.get("password"))
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

    # ------------------------------------------------------------------ mqtt
    def _on_connect(self, client, _u, _f, rc):
        if rc == 0:
            client.subscribe(self.cfg["topic_audio"], qos=1)
            log.info("subscribed %s", self.cfg["topic_audio"])
        else:
            log.error("mqtt connect rc=%s", rc)

    def _on_message(self, client, _u, msg):
        device = msg.topic.split("/")[1] if "/" in msg.topic else "unknown"
        try:
            p = json.loads(msg.payload.decode("utf-8"))
            audio = clamp_duration(b64_to_float(p["audio_b64"]), self.tcp["max_payload_s"])
            result = self.pipe.process(audio, prototype=p.get("prototype"),
                                       keyword=p.get("keyword"))
            out = self.cfg["topic_intent"].format(device=device)
            client.publish(out, json.dumps({"device_id": device, **result}), qos=1)
        except Exception as e:  # noqa: BLE001 - broker thread must never die
            client.publish(self.cfg["topic_intent"].format(device=device),
                           json.dumps({"device_id": device, "error": str(e)}), qos=1)

    # ------------------------------------------------------------------ lifecycle
    def start(self):
        self.client.connect_async(self.cfg["host"], self.cfg["port"], keepalive=30)
        self.thread = threading.Thread(target=self.client.loop_forever, daemon=True)
        self.thread.start()
        log.info("mqtt bridge -> %s:%s", self.cfg["host"], self.cfg["port"])

    def stop(self):
        self.client.disconnect()


if __name__ == "__main__":
    from .config import load_config
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    cfg = load_config()
    pipeline = AgniPipeline(cfg)
    bridge = MqttBridge(cfg, pipeline)
    bridge.start()
    threading.Event().wait()
