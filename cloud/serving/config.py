"""Config loader: cloud.yaml + environment overrides.

Env vars (12-factor style for containers):
  AGNI_API_TOKEN, AGNI_PORT, AGNI_MODEL_SIZE, AGNI_DEVICE, AGNI_COMPUTE_TYPE,
  AGNI_MQTT_ENABLED, AGNI_MQTT_HOST, AGNI_MQTT_PORT
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

_CONFIG_PATH = Path(__file__).resolve().parent.parent / "configs" / "cloud.yaml"


def _env(key: str, default: Any) -> Any:
    v = os.environ.get(key)
    return v if v not in (None, "") else default


def load_config(path: str | Path | None = None) -> dict:
    p = Path(path) if path else _CONFIG_PATH
    with open(p, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    cfg["server"]["api_token"] = _env("AGNI_API_TOKEN", cfg["server"]["api_token"])
    cfg["server"]["port"] = int(_env("AGNI_PORT", cfg["server"]["port"]))
    cfg["asr"]["model_size"] = _env("AGNI_MODEL_SIZE", cfg["asr"]["model_size"])
    cfg["asr"]["device"] = _env("AGNI_DEVICE", cfg["asr"]["device"])
    cfg["asr"]["compute_type"] = _env("AGNI_COMPUTE_TYPE", cfg["asr"]["compute_type"])
    cfg["mqtt"]["enabled"] = _env("AGNI_MQTT_ENABLED", str(cfg["mqtt"]["enabled"])).lower() in ("1", "true", "yes")
    cfg["mqtt"]["host"] = _env("AGNI_MQTT_HOST", cfg["mqtt"]["host"])
    cfg["mqtt"]["port"] = int(_env("AGNI_MQTT_PORT", cfg["mqtt"]["port"]))

    # Resolve relative paths against config dir
    cfg_dir = p.parent
    gp = cfg["intent"]["grammar_path"]
    if not Path(gp).is_absolute():
        cfg["intent"]["grammar_path"] = str(cfg_dir / gp)
    mp = cfg["verifier"]["edge_model_path"]
    if not Path(mp).is_absolute():
        cfg["verifier"]["edge_model_path"] = str((cfg_dir / mp).resolve())
    return cfg


if __name__ == "__main__":
    import json
    print(json.dumps(load_config(), indent=2))
