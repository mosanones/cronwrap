"""Tests for cronwrap.ratelimit and cronwrap.ratelimit_hook."""
from __future__ import annotations

import pytest

from cronwrap.ratelimit import (
    RateLimitConfig,
    RateLimitExceeded,
    _load_state,
    _state_path,
    check_rate_limit,
)


# ---------------------------------------------------------------------------
# RateLimitConfig validation
# ---------------------------------------------------------------------------

def test_config_valid():
    cfg = RateLimitConfig(max_runs=5, window_seconds=60)
    assert cfg.max_runs == 5
    assert cfg.window_seconds == 60


def test_config_zero_max_runs_raises():
    with pytest.raises(ValueError, match="max_runs"):
        RateLimitConfig(max_runs=0, window_seconds=60)


def test_config_negative_window_raises():
    with pytest.raises(ValueError, match="window_seconds"):
        RateLimitConfig(max_runs=1, window_seconds=-1)


# ---------------------------------------------------------------------------
# check_rate_limit – happy path
# ---------------------------------------------------------------------------

def test_first_run_is_allowed(tmp_path):
    cfg = RateLimitConfig(max_runs=3, window_seconds=60)
    # Should not raise
    check_rate_limit("job_a", cfg, store_dir=str(tmp_path), _now=1000.0)


def test_runs_within_limit_are_allowed(tmp_path):
    cfg = RateLimitConfig(max_runs=3, window_seconds=60)
    for i in range(3):
        check_rate_limit("job_b", cfg, store_dir=str(tmp_path), _now=1000.0 + i)


def test_exceeding_limit_raises(tmp_path):
    cfg = RateLimitConfig(max_runs=2, window_seconds=60)
    check_rate_limit("job_c", cfg, store_dir=str(tmp_path), _now=1000.0)
    check_rate_limit("job_c", cfg, store_dir=str(tmp_path), _now=1001.0)
    with pytest.raises(RateLimitExceeded):
        check_rate_limit("job_c", cfg, store_dir=str(tmp_path), _now=1002.0)


# ---------------------------------------------------------------------------
# Rolling window eviction
# ---------------------------------------------------------------------------

def test_old_timestamps_are_evicted(tmp_path):
    cfg = RateLimitConfig(max_runs=2, window_seconds=60)
    # Two runs at t=0 and t=1
    check_rate_limit("job_d", cfg, store_dir=str(tmp_path), _now=0.0)
    check_rate_limit("job_d", cfg, store_dir=str(tmp_path), _now=1.0)
    # Both fall outside the window when now=100 (cutoff=40)
    check_rate_limit("job_d", cfg, store_dir=str(tmp_path), _now=100.0)


def test_state_file_is_pruned_after_eviction(tmp_path):
    cfg = RateLimitConfig(max_runs=5, window_seconds=30)
    check_rate_limit("job_e", cfg, store_dir=str(tmp_path), _now=0.0)
    check_rate_limit("job_e", cfg, store_dir=str(tmp_path), _now=1.0)
    # Advance past the window
    check_rate_limit("job_e", cfg, store_dir=str(tmp_path), _now=200.0)
    path = _state_path(str(tmp_path), "job_e")
    state = _load_state(path)
    assert state.timestamps == [200.0]


# ---------------------------------------------------------------------------
# ratelimit_hook
# ---------------------------------------------------------------------------

def test_hook_does_nothing_when_env_not_set(monkeypatch, tmp_path):
    monkeypatch.delenv("CRONWRAP_RATELIMIT_MAX_RUNS", raising=False)
    monkeypatch.delenv("CRONWRAP_RATELIMIT_WINDOW_SECONDS", raising=False)
    from cronwrap.ratelimit_hook import maybe_check_rate_limit
    maybe_check_rate_limit("any_job")  # must not raise


def test_hook_raises_when_limit_exceeded(monkeypatch, tmp_path):
    monkeypatch.setenv("CRONWRAP_RATELIMIT_MAX_RUNS", "1")
    monkeypatch.setenv("CRONWRAP_RATELIMIT_WINDOW_SECONDS", "60")
    monkeypatch.setenv("CRONWRAP_RATELIMIT_STORE_DIR", str(tmp_path))
    from cronwrap.ratelimit_hook import maybe_check_rate_limit
    maybe_check_rate_limit("hook_job")
    with pytest.raises(RateLimitExceeded):
        maybe_check_rate_limit("hook_job")


def test_hook_ignores_invalid_env_values(monkeypatch):
    monkeypatch.setenv("CRONWRAP_RATELIMIT_MAX_RUNS", "not_an_int")
    monkeypatch.setenv("CRONWRAP_RATELIMIT_WINDOW_SECONDS", "60")
    from cronwrap.ratelimit_hook import maybe_check_rate_limit
    maybe_check_rate_limit("any_job")  # must not raise
