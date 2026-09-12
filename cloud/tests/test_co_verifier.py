"""Co-verifier math tests — prototype validation requires no tflite runtime."""
import numpy as np
import pytest

from serving.co_verifier import CoVerifier, mfcc_98x13


def test_rejects_bad_prototype_shape():
    v = CoVerifier(model_path=None)
    out = v.verify(np.zeros(16000, np.float32), prototype=[0.0] * 16)
    assert out["verified"] is None and "invalid" in out["note"]


def test_rejects_non_unit_prototype():
    v = CoVerifier(model_path=None)
    out = v.verify(np.zeros(16000, np.float32), prototype=[0.5] * 32)
    assert out["verified"] is None  # norm sqrt(16*0.25^2)... != 1


def test_accepts_unit_prototype_and_degrades_gracefully():
    p = np.zeros(32, np.float32); p[0] = 1.0
    v = CoVerifier(model_path=None)  # no interpreter in CI
    out = v.verify(np.zeros(16000, np.float32), prototype=p.tolist())
    assert out["verified"] in (None, False)
    assert "verifier" in out.get("note", "verifier")


def test_refuse_policy_vetoes():
    p = np.zeros(32, np.float32); p[1] = -1.0
    v = CoVerifier(model_path=None, degraded="refuse")
    out = v.verify(np.zeros(16000, np.float32), prototype=p.tolist())
    assert out["verified"] is False


def test_mfcc_shape():
    x = np.random.default_rng(0).standard_normal(16000).astype(np.float32)
    m = mfcc_98x13(x)
    assert m.shape == (98, 13, 1) and m.dtype == np.float32
    assert np.isfinite(m).all()
