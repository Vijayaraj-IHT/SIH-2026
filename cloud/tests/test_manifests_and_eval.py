"""Manifest builder + offline intent-eval tests on tiny synthetic fixtures."""
import json
from pathlib import Path

import numpy as np
import soundfile as sf

from data.make_manifests import (norm_text, scan_command_corpus,
                                 scan_librispeech)
from evaluation.eval_command_intent import score_rows
from serving.intent_router import IntentRouter

GRAMMAR = Path(__file__).resolve().parent.parent / "configs" / "commands.yaml"


def _fake_ls(tmp_path: Path):
    root = tmp_path / "LibriSpeech" / "dev-clean" / "1272" / "128104"
    root.mkdir(parents=True)
    for i in range(2):
        sf.write(root / f"1272-128104-000{i}.flac", np.zeros(16000, np.float32), 16000,
                 format="FLAC")
    (root / "1272-128104.trans.txt").write_text(
        "1272-128104-0000 HELLO WORLD, MY FRIEND!\n1272-128104-0001 A SECOND LINE\n")
    return tmp_path


def test_norm_text():
    assert norm_text("  Telemetry, Channel: Five! ") == "telemetry channel five"
    assert norm_text("don't stop") == "don't stop"


def test_scan_librispeech(tmp_path):
    rows = scan_librispeech(_fake_ls(tmp_path))
    assert len(rows) == 2
    assert rows[0]["split"] == "dev"
    assert rows[0]["text"] == "hello world my friend"
    assert rows[0]["speaker"] == "1272"


def test_scan_command_corpus_finds_audio_priority(tmp_path):
    meta = tmp_path / "metadata.csv"
    meta.write_text("id,text,action,subsystem,split,status\n"
                    "AGNI_0001,read telemetry channel five,read,telemetry,test,pending\n"
                    "AGNI_0002,abort payload,abort,payload,train,pending\n")
    rec = tmp_path / "recordings" / "alice"
    rec.mkdir(parents=True)
    sf.write(rec / "AGNI_0001.wav", np.zeros(16000, np.float32), 16000)
    rows = scan_command_corpus(meta, [tmp_path / "recordings"])
    assert rows[0]["audio_path"].endswith("AGNI_0001.wav")
    assert rows[0]["status"] == "ready"
    assert rows[1]["status"] == "pending"


def test_intent_scoring_offline():
    router = IntentRouter(GRAMMAR)
    rows = [
        {"text": "agni read telemetry channel five",
         "hypothesis": "read telemetry channel five",
         "reference_intent": {"action": "read", "subsystem": "telemetry", "channel": "five"}},
        {"text": "abort payload",
         "hypothesis": "abort payload",
         "reference_intent": {"action": "abort", "subsystem": "payload"}},
        {"text": "set heater voltage to three point three",
         "hypothesis": "set heater voltage to three point three",
         "reference_intent": {"action": "set", "subsystem": "heater",
                              "voltage": "three point three"}},
        {"text": "switch transponder to silent mode",
         "hypothesis": "switch transponder to idle mode",   # deliberate miss
         "reference_intent": {"action": "switch", "subsystem": "transponder",
                              "mode": "silent"}},
    ]
    res = score_rows(rows, router)
    assert res["total"] == 4
    assert res["exact_match"] == 3
    assert res["intent_accuracy"] == 0.75
    assert res["sample_failures"][0]["route"]["mode"] == "idle"
