"""Tests for circuit_breaker, circuit_breaker_hook, and circuit_breaker_cli."""
from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone, timedelta

import pytest

from cronwrap.circuit_breaker import (
    CircuitBreakerConfig,
    CircuitOpen,
    CircuitState,
    check_circuit,
    load_state,
    record_outcome,
    save_state,
)
from cronwrap.circuit_breaker_cli import (
    render_all_circuits,
    render_circuit_state,
    render_open_circuits,
)
from cronwrap.executor import ExecutionResult
from cronwrap.circuit_breaker_hook import maybe_check, maybe_record


@pytest.fixture()
def store(tmp_path):
    return str(tmp_path / "circuit")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _cfg(**kw) -> CircuitBreakerConfig:
    return CircuitBreakerConfig(**kw)


# --- config validation ---

def test_config_valid():
    cfg = _cfg(max_failures=2, reset_after=60)
    assert cfg.max_failures == 2


def test_config_zero_max_failures_raises():
    with pytest.raises(ValueError):
        _cfg(max_failures=0)


def test_config_negative_reset_after_raises():
    with pytest.raises(ValueError):
        _cfg(reset_after=-1)


# --- load / save ---

def test_load_missing_returns_closed(store):
    state = load_state(store, "myjob")
    assert state.state == "closed"
    assert state.consecutive_failures == 0


def test_save_and_load_roundtrip(store):
    s = CircuitState(job_name="j", consecutive_failures=2, state="open", opened_at=_now())
    save_state(store, s)
    loaded = load_state(store, "j")
    assert loaded.consecutive_failures == 2
    assert loaded.state == "open"


# --- record_outcome ---

def test_success_resets_failures(store):
    cfg = _cfg(max_failures=3)
    record_outcome(store, "j", False, cfg, _now())
    record_outcome(store, "j", False, cfg, _now())
    record_outcome(store, "j", True, cfg, _now())
    state = load_state(store, "j")
    assert state.consecutive_failures == 0
    assert state.state == "closed"


def test_failures_open_circuit(store):
    cfg = _cfg(max_failures=2)
    record_outcome(store, "j", False, cfg, _now())
    record_outcome(store, "j", False, cfg, _now())
    state = load_state(store, "j")
    assert state.state == "open"
    assert state.opened_at is not None


# --- check_circuit ---

def test_closed_circuit_does_not_raise(store):
    cfg = _cfg(max_failures=3)
    check_circuit(store, "j", cfg, time.time())  # no exception


def test_open_circuit_raises(store):
    cfg = _cfg(max_failures=1, reset_after=9999)
    record_outcome(store, "j", False, cfg, _now())
    with pytest.raises(CircuitOpen):
        check_circuit(store, "j", cfg, time.time())


def test_open_circuit_after_reset_becomes_half_open(store):
    cfg = _cfg(max_failures=1, reset_after=0)
    old_time = (datetime.now(timezone.utc) - timedelta(seconds=10)).isoformat()
    record_outcome(store, "j", False, cfg, old_time)
    check_circuit(store, "j", cfg, time.time())  # should not raise
    state = load_state(store, "j")
    assert state.state == "half-open"


# --- hook ---

def test_hook_maybe_record_success(store, monkeypatch):
    monkeypatch.setenv("CRONWRAP_CB_MAX_FAILURES", "3")
    result = ExecutionResult(exit_code=0, stdout="", stderr="", duration=1.0, timed_out=False)
    maybe_record("j", result, store_dir=store)
    state = load_state(store, "j")
    assert state.state == "closed"


# --- cli ---

def test_render_circuit_state_closed(store):
    state = CircuitState(job_name="myjob")
    out = render_circuit_state(state)
    assert "CLOSED" in out
    assert "myjob" in out


def test_render_all_circuits_empty(store):
    out = render_all_circuits(store)
    assert "No circuit" in out


def test_render_open_circuits_filters(store):
    cfg = _cfg(max_failures=1, reset_after=9999)
    record_outcome(store, "bad_job", False, cfg, _now())
    record_outcome(store, "good_job", True, cfg, _now())
    out = render_open_circuits(store)
    assert "bad_job" in out
    assert "good_job" not in out
