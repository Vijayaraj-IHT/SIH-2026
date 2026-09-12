"""Augmentation math tests — power-accurate SNR, channel shaping, determinism."""
import numpy as np
import pytest

from data.channel_augment import (ChannelAug, add_noise, bandpass_channel,
                                  gain_jitter, make_rir, quantize_int16,
                                  speed_perturb)


def tone(freq=440.0, dur=1.0, sr=16000):
    t = np.arange(int(dur * sr)) / sr
    return (0.5 * np.sin(2 * np.pi * freq * t)).astype(np.float32)


def test_snr_is_power_exact():
    rng = np.random.default_rng(1)
    x, n = tone(), rng.standard_normal(64000).astype(np.float32)
    y = add_noise(x, n, 10.0, rng)
    # measured SNR of (x, y-x) must match 10 dB within tolerance
    ns = y - x
    snr = 10 * np.log10(np.mean(x**2) / np.mean(ns**2))
    assert abs(snr - 10.0) < 0.5


def test_speed_perturb_length():
    x = tone(dur=2.0)
    assert abs(len(speed_perturb(x, 1.1)) - len(x) / 1.1) < 2
    assert len(speed_perturb(x, 1.0)) == len(x)


def test_bandpass_kills_out_of_band():
    lo, hi = tone(20.0), tone(1000.0)
    y_lo, y_hi = bandpass_channel(lo), bandpass_channel(hi)
    assert np.mean(y_lo**2) < 1e-4            # >=30 dB rejection of 20 Hz
    assert np.mean(y_hi**2) > 0.10            # 1 kHz passes


def test_quantize_int16_grid():
    y = quantize_int16(np.linspace(-1, 1, 1001).astype(np.float32))
    assert np.all(np.abs((y * 32767.0) - np.round(y * 32767.0)) < 1e-3)
    assert y.max() <= 1.0 and y.min() >= -1.0


def test_gain_jitter_clips():
    x = np.full(100, 0.9, np.float32)
    assert gain_jitter(x, 12.0).max() == pytest.approx(1.0)


def test_chain_determinism_and_shape():
    rng1, rng2 = np.random.default_rng(42), np.random.default_rng(42)
    aug = ChannelAug(noise_pool=[np.random.default_rng(0).standard_normal(32000).astype(np.float32)])
    x = tone(dur=1.0)
    y1, y2 = aug(x, rng1), aug(x, rng2)
    assert np.array_equal(y1, y2)
    assert y1.size > 0 and np.isfinite(y1).all()


def test_rir_norm_and_direct_path():
    rir = make_rir(0.3, rng=np.random.default_rng(3))
    assert np.linalg.norm(rir) == pytest.approx(1.0, abs=1e-5)
    assert int(np.argmax(np.abs(rir))) == int(0.003 * 16000)   # direct path dominates
    assert np.abs(rir[-1]) < 0.05 * np.abs(rir).max()          # decayed by RT60
