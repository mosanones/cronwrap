"""Tests for cronwrap.audit, cronwrap.audit_hook, and cronwrap.audit_report."""
from __future__ import annotations

import json
import os
from unittest.mock import MagicMock

import pytest

from cronwrap.audit import AuditEvent, append_event, load_events, make_event
from cronwrap.audit_hook import record_alert_sent, record_job_end, record_job_start
from cronwrap.audit_report import render_event, render_events, render_summary
from cronwrap.executor import ExecutionResult


@pytest.fixture()
def audit_path(tmp_path):
    return str(tmp_path / "audit.jsonl")


def _make_result(exit_code=0, timed_out=False, stderr="", duration=1.5):
    return ExecutionResult(
        exit_code=exit_code,
        stdout="out",
        stderr=stderr,
        duration_seconds=duration,
        timed_out=timed_out,
    )


# --- audit module ---

def test_load_events_missing_file(audit_path):
    assert load_events(audit_path) == []


def test_append_and_load_roundtrip(audit_path):
    ev = make_event("job_success", "myjob", exit_code=0, duration_seconds=2.1)
    append_event(ev, path=audit_path)
    loaded = load_events(audit_path)
    assert len(loaded) == 1
    assert loaded[0].event_type == "job_success"
    assert loaded[0].job_name == "myjob"
    assert loaded[0].exit_code == 0


def test_load_events_filter_by_job(audit_path):
    append_event(make_event("job_success", "alpha"), path=audit_path)
    append_event(make_event("job_failure", "beta"), path=audit_path)
    result = load_events(audit_path, job_name="alpha")
    assert all(e.job_name == "alpha" for e in result)
    assert len(result) == 1


def test_load_events_filter_by_type(audit_path):
    append_event(make_event("job_start", "alpha"), path=audit_path)
    append_event(make_event("job_success", "alpha"), path=audit_path)
    result = load_events(audit_path, event_type="job_start")
    assert len(result) == 1
    assert result[0].event_type == "job_start"


def test_load_events_skips_corrupt_lines(audit_path):
    with open(audit_path, "w") as fh:
        fh.write("not-json\n")
        fh.write(json.dumps({"timestamp": "t", "event_type": "job_start",
                              "job_name": "x", "detail": None,
                              "exit_code": None, "duration_seconds": None}) + "\n")
    events = load_events(audit_path)
    assert len(events) == 1


def test_load_events_limit(audit_path):
    for i in range(10):
        append_event(make_event("job_success", f"job{i}"), path=audit_path)
    result = load_events(audit_path, limit=3)
    assert len(result) == 3


# --- audit_hook ---

def test_record_job_start(audit_path):
    record_job_start("myjob", "echo hi", audit_path=audit_path)
    events = load_events(audit_path)
    assert events[0].event_type == "job_start"
    assert "echo hi" in events[0].detail


def test_record_job_end_success(audit_path):
    record_job_end("myjob", _make_result(exit_code=0), audit_path=audit_path)
    events = load_events(audit_path)
    assert events[0].event_type == "job_success"


def test_record_job_end_failure(audit_path):
    record_job_end("myjob", _make_result(exit_code=1, stderr="oops"), audit_path=audit_path)
    events = load_events(audit_path)
    assert events[0].event_type == "job_failure"
    assert events[0].detail == "oops"


def test_record_job_end_timeout(audit_path):
    record_job_end("myjob", _make_result(timed_out=True, exit_code=-1), audit_path=audit_path)
    events = load_events(audit_path)
    assert events[0].event_type == "job_timeout"


def test_record_alert_sent(audit_path):
    record_alert_sent("myjob", "email", audit_path=audit_path)
    events = load_events(audit_path)
    assert events[0].event_type == "alert_sent"
    assert "email" in events[0].detail


# --- audit_report ---

def test_render_event_success():
    ev = AuditEvent(timestamp="2024-01-01T00:00:00+00:00",
                    event_type="job_success", job_name="myjob",
                    exit_code=0, duration_seconds=1.234, detail=None)
    line = render_event(ev)
    assert "job_success" in line
    assert "myjob" in line
    assert "1.234s" in line


def test_render_events_empty():
    assert render_events([]) == "(no audit events)"


def test_render_summary_counts():
    events = [
        AuditEvent("t", "job_success", "a", None, 0, 1.0),
        AuditEvent("t", "job_success", "b", None, 0, 1.0),
        AuditEvent("t", "job_failure", "c", None, 1, 1.0),
    ]
    summary = render_summary(events)
    assert "job_success=2" in summary
    assert "job_failure=1" in summary
