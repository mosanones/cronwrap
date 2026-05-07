"""Tests for heartbeat tracking, hook, and CLI rendering."""
from __future__ import annotations

import datetime
import json
from pathlib import Path

import pytest

from cronwrap.heartbeat import (
    HeartbeatRecord,
    load_heartbeats,
    save_heartbeats,
    ping,
    check_missed,
)
from cronwrap.heartbeat_hook import maybe_ping
from cronwrap.heartbeat_cli import render_heartbeat, render_all_heartbeats, render_missed_heartbeats


@pytest.fixture()
def store(tmp_path: Path) -> str:
    return str(tmp_path)


# ── heartbeat core ──────────────────────────────────────────────────────────

def test_load_missing_file_returns_empty(store):
    assert load_heartbeats(store) == {}


def test_load_corrupt_file_returns_empty(store):
    (Path(store) / "heartbeats.json").write_text("not-json")
    assert load_heartbeats(store) == {}


def test_ping_creates_record(store):
    record = ping(store, "backup", 3600)
    assert record.job_name == "backup"
    assert record.interval_seconds == 3600
    assert not record.missed
    loaded = load_heartbeats(store)
    assert "backup" in loaded


def test_ping_updates_existing(store):
    ping(store, "backup", 3600)
    r2 = ping(store, "backup", 7200)
    assert r2.interval_seconds == 7200
    assert len(load_heartbeats(store)) == 1


def test_check_missed_on_time(store):
    ping(store, "fast_job", 9999)
    assert check_missed(store) == []


def test_check_missed_detects_overdue(store):
    old_ts = (
        datetime.datetime.now(datetime.timezone.utc)
        - datetime.timedelta(seconds=200)
    ).isoformat()
    records = {"slow": HeartbeatRecord("slow", old_ts, 60)}
    save_heartbeats(store, records)
    missed = check_missed(store)
    assert len(missed) == 1
    assert missed[0].job_name == "slow"
    assert missed[0].missed is True


# ── heartbeat hook ──────────────────────────────────────────────────────────

def test_maybe_ping_skips_on_failure(store):
    result = maybe_ping("job", succeeded=False, store_dir=store, interval_seconds=60)
    assert result is None


def test_maybe_ping_skips_without_interval(store):
    result = maybe_ping("job", succeeded=True, store_dir=store, interval_seconds=None)
    assert result is None


def test_maybe_ping_records_on_success(store):
    result = maybe_ping("job", succeeded=True, store_dir=store, interval_seconds=300)
    assert result is not None
    assert result.job_name == "job"


def test_maybe_ping_reads_env_interval(store, monkeypatch):
    monkeypatch.setenv("CRONWRAP_HEARTBEAT_INTERVAL", "120")
    result = maybe_ping("job", succeeded=True, store_dir=store)
    assert result is not None
    assert result.interval_seconds == 120


# ── heartbeat CLI ───────────────────────────────────────────────────────────

def test_render_heartbeat_healthy():
    r = HeartbeatRecord("myjob", datetime.datetime.now(datetime.timezone.utc).isoformat(), 600)
    out = render_heartbeat(r)
    assert "💚" in out
    assert "myjob" in out


def test_render_heartbeat_missed():
    r = HeartbeatRecord("myjob", datetime.datetime.now(datetime.timezone.utc).isoformat(), 600, missed=True)
    out = render_heartbeat(r)
    assert "💔" in out


def test_render_all_heartbeats_empty(store):
    out = render_all_heartbeats(store)
    assert "No heartbeat records" in out


def test_render_missed_none(store):
    ping(store, "ok_job", 99999)
    out = render_missed_heartbeats(store)
    assert "on time" in out
