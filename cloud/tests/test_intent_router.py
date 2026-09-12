"""Deterministic grammar parser tests — no heavy deps (numpy-free, model-free)."""
from pathlib import Path

import pytest

from serving.intent_router import IntentRouter, normalize

HERE = Path(__file__).resolve().parent.parent / "configs" / "commands.yaml"


@pytest.fixture(scope="module")
def r():
    return IntentRouter(HERE)


def test_normalize_numbers():
    assert normalize("Channel Five") == "channel 5"
    assert normalize("channel twenty three") == "channel 23"
    assert normalize("set voltage to three point three") == "set voltage to 3 point 3"


@pytest.mark.parametrize("text,action,sub,extra", [
    ("agni read telemetry channel five", "read", "telemetry", {"channel": 5}),
    ("read telemetry", "read", "telemetry", {}),
    ("vayu deploy the solar panel", "deploy", "solar_panel", {}),
    ("jump abort payload", "abort", "payload", {}),
    ("cable retract the antenna", "stow", "antenna", {}),
    ("calibrate thruster", "calibrate", "thruster", {}),
    ("helios get battery voltage", "read", "battery", {}),
    ("zora switch transponder to silent mode", "switch", "transponder", {"mode": "silent"}),
    ("switch camera to science mode", "switch", "camera", {"mode": "science"}),
])
def test_commands(r, text, action, sub, extra):
    i = r.parse(text)
    assert i["type"] == "command"
    assert i["action"] == action
    assert i["subsystem"] == sub
    for k, v in extra.items():
        assert i[k] == v


def test_voltage(r):
    i = r.parse("set heater voltage to three point three")
    assert i["type"] == "command" and i["voltage"] == pytest.approx(3.3)


def test_freeform_fallback(r):
    i = r.parse("what is the battery temperature trend")
    assert i["type"] == "freeform"
    i = r.parse("")
    assert i["type"] == "freeform"


def test_do_not_swallow_keywordless_echo(r):
    # "jumper" is NOT the enrolled keyword "jump" — word-boundary check
    i = r.parse("jumper cable status")
    assert i["type"] != "command" or i.get("subsystem") is None
