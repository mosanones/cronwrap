"""Tests for cronwrap.jitter."""

from __future__ import annotations

import pytest

from cronwrap.jitter import JitterConfig, apply_jitter, sample_delay


# ---------------------------------------------------------------------------
# JitterConfig validation
# ---------------------------------------------------------------------------

def test_default_config_is_disabled():
    cfg = JitterConfig()
    assert not cfg.enabled
    assert cfg.max_seconds == 0.0


def test_config_enabled_when_max_positive():
    cfg = JitterConfig(max_seconds=5.0)
    assert cfg.enabled


def test_config_negative_min_raises():
    with pytest.raises(ValueError, match="min_seconds"):
        JitterConfig(min_seconds=-1.0, max_seconds=5.0)


def test_config_negative_max_raises():
    with pytest.raises(ValueError, match="max_seconds"):
        JitterConfig(max_seconds=-1.0)


def test_config_min_greater_than_max_raises():
    with pytest.raises(ValueError, match="min_seconds must be <= max_seconds"):
        JitterConfig(min_seconds=10.0, max_seconds=5.0)


def test_config_min_equal_to_max_is_valid():
    cfg = JitterConfig(min_seconds=3.0, max_seconds=3.0)
    assert cfg.enabled


# ---------------------------------------------------------------------------
# sample_delay
# ---------------------------------------------------------------------------

def test_sample_delay_disabled_returns_zero():
    cfg = JitterConfig(max_seconds=0.0)
    assert sample_delay(cfg) == 0.0


def test_sample_delay_within_bounds():
    cfg = JitterConfig(min_seconds=1.0, max_seconds=4.0)
    for _ in range(50):
        d = sample_delay(cfg)
        assert 1.0 <= d <= 4.0


def test_sample_delay_deterministic_with_seed():
    cfg = JitterConfig(min_seconds=0.0, max_seconds=10.0, seed=42)
    d1 = sample_delay(cfg)
    d2 = sample_delay(cfg)
    assert d1 == d2


def test_sample_delay_exact_when_min_equals_max():
    cfg = JitterConfig(min_seconds=2.5, max_seconds=2.5)
    assert sample_delay(cfg) == pytest.approx(2.5)


# ---------------------------------------------------------------------------
# apply_jitter
# ---------------------------------------------------------------------------

def test_apply_jitter_disabled_does_not_sleep():
    slept = []
    cfg = JitterConfig(max_seconds=0.0)
    delay = apply_jitter(cfg, _sleep=slept.append)
    assert delay == 0.0
    assert slept == []


def test_apply_jitter_calls_sleep_with_sampled_delay():
    slept = []
    cfg = JitterConfig(min_seconds=1.0, max_seconds=1.0)  # deterministic
    delay = apply_jitter(cfg, _sleep=slept.append)
    assert delay == pytest.approx(1.0)
    assert len(slept) == 1
    assert slept[0] == pytest.approx(1.0)


def test_apply_jitter_returns_actual_delay():
    slept = []
    cfg = JitterConfig(min_seconds=0.5, max_seconds=3.0, seed=7)
    delay = apply_jitter(cfg, _sleep=slept.append)
    assert 0.5 <= delay <= 3.0
    assert slept == [delay]
