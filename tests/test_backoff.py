"""Tests for cronwrap.backoff."""

from __future__ import annotations

import itertools
import math
import pytest

from cronwrap.backoff import BackoffConfig, compute_delay, delay_sequence


# ---------------------------------------------------------------------------
# BackoffConfig validation
# ---------------------------------------------------------------------------

def test_default_config_is_valid():
    cfg = BackoffConfig()
    assert cfg.strategy == "exponential"
    assert cfg.base_delay == 1.0
    assert cfg.jitter is True


def test_invalid_strategy_raises():
    with pytest.raises(ValueError, match="strategy"):
        BackoffConfig(strategy="random_walk")


def test_base_delay_zero_raises():
    with pytest.raises(ValueError, match="base_delay"):
        BackoffConfig(base_delay=0)


def test_max_delay_less_than_base_raises():
    with pytest.raises(ValueError, match="max_delay"):
        BackoffConfig(base_delay=10.0, max_delay=5.0)


def test_multiplier_zero_raises():
    with pytest.raises(ValueError, match="multiplier"):
        BackoffConfig(multiplier=0)


# ---------------------------------------------------------------------------
# compute_delay – fixed strategy
# ---------------------------------------------------------------------------

def test_fixed_strategy_returns_base_delay():
    cfg = BackoffConfig(strategy="fixed", base_delay=5.0, jitter=False)
    for attempt in range(5):
        assert compute_delay(cfg, attempt) == pytest.approx(5.0)


# ---------------------------------------------------------------------------
# compute_delay – linear strategy
# ---------------------------------------------------------------------------

def test_linear_strategy_grows_linearly():
    cfg = BackoffConfig(strategy="linear", base_delay=2.0, multiplier=3.0, jitter=False)
    assert compute_delay(cfg, 0) == pytest.approx(2.0)
    assert compute_delay(cfg, 1) == pytest.approx(5.0)
    assert compute_delay(cfg, 2) == pytest.approx(8.0)


# ---------------------------------------------------------------------------
# compute_delay – exponential strategy
# ---------------------------------------------------------------------------

def test_exponential_strategy_grows_exponentially():
    cfg = BackoffConfig(strategy="exponential", base_delay=1.0, multiplier=2.0, jitter=False)
    assert compute_delay(cfg, 0) == pytest.approx(1.0)
    assert compute_delay(cfg, 1) == pytest.approx(2.0)
    assert compute_delay(cfg, 3) == pytest.approx(8.0)


def test_delay_is_capped_at_max():
    cfg = BackoffConfig(strategy="exponential", base_delay=1.0, multiplier=10.0,
                        max_delay=50.0, jitter=False)
    assert compute_delay(cfg, 10) == pytest.approx(50.0)


# ---------------------------------------------------------------------------
# Jitter
# ---------------------------------------------------------------------------

def test_jitter_produces_variation():
    cfg = BackoffConfig(strategy="fixed", base_delay=100.0, jitter=True)
    delays = {compute_delay(cfg, 0) for _ in range(30)}
    # With jitter we expect more than one distinct value across 30 samples
    assert len(delays) > 1


def test_jitter_stays_within_20_percent():
    cfg = BackoffConfig(strategy="fixed", base_delay=100.0, jitter=True)
    for _ in range(100):
        d = compute_delay(cfg, 0)
        assert 80.0 <= d <= 120.0


# ---------------------------------------------------------------------------
# delay_sequence
# ---------------------------------------------------------------------------

def test_delay_sequence_yields_increasing_values_exponential():
    cfg = BackoffConfig(strategy="exponential", base_delay=1.0, multiplier=2.0,
                        max_delay=1000.0, jitter=False)
    seq = list(itertools.islice(delay_sequence(cfg), 6))
    for a, b in zip(seq, seq[1:]):
        assert b >= a


def test_delay_sequence_is_infinite():
    cfg = BackoffConfig(strategy="fixed", base_delay=1.0, jitter=False)
    seq = itertools.islice(delay_sequence(cfg), 1000)
    assert sum(1 for _ in seq) == 1000
