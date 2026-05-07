"""Tests for cronwrap.snapshot and cronwrap.snapshot_hook."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from cronwrap.snapshot import (
    JobSnapshot,
    load_snapshot,
    save_snapshot,
    update_snapshot,
    state_changed,
    _snapshot_path,
)
from cronwrap.snapshot_hook import record_snapshot
from cronwrap.executor import ExecutionResult


@pytest.fixture()
def store(tmp_path):
    return str(tmp_path / "snapshots")


def _result(exit_code=0, timed_out=False, duration=1.5):
    return ExecutionResult(
        exit_code=exit_code,
        stdout="out",
        stderr="err",
        duration_seconds=duration,
        timed_out=timed_out,
    )


# ── snapshot persistence ────────────────────────────────────────────────────

def test_load_missing_returns_none(store):
    assert load_snapshot(store, "myjob") is None


def test_save_and_load_roundtrip(store):
    snap = JobSnapshot(
        job_name="backup",
        last_exit_code=0,
        last_status="success",
        last_run_at="2024-01-01T00:00:00",
        consecutive_failures=0,
        last_duration_seconds=3.14,
    )
    save_snapshot(store, snap)
    loaded = load_snapshot(store, "backup")
    assert loaded is not None
    assert loaded.job_name == "backup"
    assert loaded.last_duration_seconds == pytest.approx(3.14)


def test_load_corrupt_file_returns_none(store):
    path = _snapshot_path(store, "bad")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("not-json")
    assert load_snapshot(store, "bad") is None


# ── update_snapshot ─────────────────────────────────────────────────────────

def test_update_snapshot_first_success(store):
    snap = update_snapshot(store, "j", 0, "success", "2024-01-01T00:00:00", 1.0)
    assert snap.consecutive_failures == 0
    assert snap.last_status == "success"


def test_update_snapshot_first_failure(store):
    snap = update_snapshot(store, "j", 1, "failure", "2024-01-01T00:00:00", 1.0)
    assert snap.consecutive_failures == 1


def test_update_snapshot_increments_consecutive(store):
    update_snapshot(store, "j", 1, "failure", "2024-01-01T00:00:00", 1.0)
    snap = update_snapshot(store, "j", 1, "failure", "2024-01-01T01:00:00", 1.0)
    assert snap.consecutive_failures == 2


def test_update_snapshot_resets_on_success(store):
    update_snapshot(store, "j", 1, "failure", "2024-01-01T00:00:00", 1.0)
    snap = update_snapshot(store, "j", 0, "success", "2024-01-01T01:00:00", 1.0)
    assert snap.consecutive_failures == 0


# ── state_changed ────────────────────────────────────────────────────────────

def test_state_changed_no_previous():
    snap = JobSnapshot("j", 0, "success", "2024-01-01T00:00:00")
    assert state_changed(None, snap) is True


def test_state_changed_same_status():
    prev = JobSnapshot("j", 0, "success", "2024-01-01T00:00:00")
    curr = JobSnapshot("j", 0, "success", "2024-01-01T01:00:00")
    assert state_changed(prev, curr) is False


def test_state_changed_different_status():
    prev = JobSnapshot("j", 0, "success", "2024-01-01T00:00:00")
    curr = JobSnapshot("j", 1, "failure", "2024-01-01T01:00:00")
    assert state_changed(prev, curr) is True


# ── snapshot_hook ────────────────────────────────────────────────────────────

def test_hook_success_result(store):
    snap, changed = record_snapshot("myjob", _result(0), "2024-01-01T00:00:00", store)
    assert snap.last_status == "success"
    assert changed is True  # first run always changed


def test_hook_failure_result(store):
    snap, _ = record_snapshot("myjob", _result(1), "2024-01-01T00:00:00", store)
    assert snap.last_status == "failure"
    assert snap.consecutive_failures == 1


def test_hook_timeout_result(store):
    snap, _ = record_snapshot("myjob", _result(1, timed_out=True), "2024-01-01T00:00:00", store)
    assert snap.last_status == "timeout"


def test_hook_detects_change(store):
    record_snapshot("myjob", _result(0), "2024-01-01T00:00:00", store)
    _, changed = record_snapshot("myjob", _result(1), "2024-01-01T01:00:00", store)
    assert changed is True


def test_hook_no_change(store):
    record_snapshot("myjob", _result(0), "2024-01-01T00:00:00", store)
    _, changed = record_snapshot("myjob", _result(0), "2024-01-01T01:00:00", store)
    assert changed is False
