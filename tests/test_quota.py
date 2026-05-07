"""Tests for cronwrap.quota and cronwrap.quota_hook."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from cronwrap.quota import (
    QuotaConfig,
    QuotaExceeded,
    _QuotaState,
    _state_path,
    check_quota,
    load_quota_state,
)
from cronwrap.quota_hook import maybe_check_quota


# ---------------------------------------------------------------------------
# QuotaConfig
# ---------------------------------------------------------------------------

def test_config_valid():
    cfg = QuotaConfig(max_runs=5, period="daily")
    assert cfg.max_runs == 5
    assert cfg.period == "daily"


def test_config_zero_max_runs_raises():
    with pytest.raises(ValueError, match="max_runs"):
        QuotaConfig(max_runs=0, period="daily")


def test_config_invalid_period_raises():
    with pytest.raises(ValueError, match="period"):
        QuotaConfig(max_runs=1, period="yearly")


def test_period_key_daily():
    cfg = QuotaConfig(max_runs=1, period="daily")
    dt = datetime(2024, 6, 15, 10, 30, tzinfo=timezone.utc)
    assert cfg.period_key(dt) == "2024-06-15"


def test_period_key_hourly():
    cfg = QuotaConfig(max_runs=1, period="hourly")
    dt = datetime(2024, 6, 15, 10, 30, tzinfo=timezone.utc)
    assert cfg.period_key(dt) == "2024-06-15T10"


def test_period_key_monthly():
    cfg = QuotaConfig(max_runs=1, period="monthly")
    dt = datetime(2024, 6, 15, tzinfo=timezone.utc)
    assert cfg.period_key(dt) == "2024-06"


# ---------------------------------------------------------------------------
# check_quota
# ---------------------------------------------------------------------------

@pytest.fixture()
def store(tmp_path: Path) -> Path:
    return tmp_path


def test_first_run_is_allowed(store):
    cfg = QuotaConfig(max_runs=3, period="daily")
    check_quota("myjob", cfg, base_dir=str(store))  # should not raise


def test_runs_within_limit_are_allowed(store):
    cfg = QuotaConfig(max_runs=3, period="daily")
    for _ in range(3):
        check_quota("myjob", cfg, base_dir=str(store))


def test_exceeding_limit_raises(store):
    cfg = QuotaConfig(max_runs=2, period="daily")
    check_quota("myjob", cfg, base_dir=str(store))
    check_quota("myjob", cfg, base_dir=str(store))
    with pytest.raises(QuotaExceeded, match="myjob"):
        check_quota("myjob", cfg, base_dir=str(store))


def test_corrupt_state_file_resets(store):
    path = _state_path("myjob", str(store))
    path.write_text("not-json")
    cfg = QuotaConfig(max_runs=2, period="daily")
    check_quota("myjob", cfg, base_dir=str(store))  # should not raise


def test_new_period_resets_counter(store):
    cfg = QuotaConfig(max_runs=1, period="daily")
    # Manually write a state for yesterday
    path = _state_path("myjob", str(store))
    old_state = _QuotaState(period_key="2000-01-01", runs=1, timestamps=[])
    path.write_text(json.dumps(old_state.__dict__))
    # Today's run should be allowed
    check_quota("myjob", cfg, base_dir=str(store))


def test_load_quota_state_missing_returns_none(store):
    assert load_quota_state("ghost", base_dir=str(store)) is None


def test_load_quota_state_after_run(store):
    cfg = QuotaConfig(max_runs=5, period="daily")
    check_quota("myjob", cfg, base_dir=str(store))
    state = load_quota_state("myjob", base_dir=str(store))
    assert state is not None
    assert state.runs == 1


# ---------------------------------------------------------------------------
# quota_hook
# ---------------------------------------------------------------------------

def test_maybe_check_quota_no_env_passes(store, monkeypatch):
    monkeypatch.delenv("CRONWRAP_QUOTA_MAX_RUNS", raising=False)
    maybe_check_quota("myjob", base_dir=str(store))  # should not raise


def test_maybe_check_quota_with_env_enforces(store, monkeypatch):
    monkeypatch.setenv("CRONWRAP_QUOTA_MAX_RUNS", "1")
    monkeypatch.setenv("CRONWRAP_QUOTA_PERIOD", "daily")
    maybe_check_quota("myjob", base_dir=str(store))
    with pytest.raises(QuotaExceeded):
        maybe_check_quota("myjob", base_dir=str(store))


def test_maybe_check_quota_bad_env_is_ignored(store, monkeypatch):
    monkeypatch.setenv("CRONWRAP_QUOTA_MAX_RUNS", "not-a-number")
    maybe_check_quota("myjob", base_dir=str(store))  # should not raise
