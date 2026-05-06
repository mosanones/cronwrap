"""Focused rendering tests for cronwrap.audit_report."""
from __future__ import annotations

from cronwrap.audit import AuditEvent
from cronwrap.audit_report import _icon, render_event, render_events, render_summary


def _ev(event_type="job_success", job_name="job", exit_code=None,
        duration=None, detail=None):
    return AuditEvent(
        timestamp="2024-06-01T12:00:00+00:00",
        event_type=event_type,
        job_name=job_name,
        detail=detail,
        exit_code=exit_code,
        duration_seconds=duration,
    )


def test_icon_known_types():
    assert _icon("job_start") == "▶"
    assert _icon("job_success") == "✓"
    assert _icon("job_failure") == "✗"
    assert _icon("job_timeout") == "⏱"
    assert _icon("alert_sent") == "✉"


def test_icon_unknown_type():
    assert _icon("unknown_event") == "•"


def test_render_event_includes_timestamp():
    ev = _ev()
    assert "2024-06-01" in render_event(ev)


def test_render_event_includes_job_name():
    ev = _ev(job_name="backup_job")
    assert "backup_job" in render_event(ev)


def test_render_event_no_optional_fields():
    ev = _ev(event_type="job_start")
    line = render_event(ev)
    assert "job_start" in line
    # no exit_code or duration
    assert "exit=" not in line
    assert "s" not in line.split("job_start")[1].split("  ")[0]


def test_render_event_with_detail():
    ev = _ev(event_type="job_failure", detail="disk full", exit_code=1, duration=0.5)
    line = render_event(ev)
    assert "disk full" in line
    assert "exit=1" in line


def test_render_events_multiple():
    events = [_ev("job_start"), _ev("job_success")]
    output = render_events(events)
    assert "job_start" in output
    assert "job_success" in output
    assert output.count("\n") == 1  # two lines separated by newline


def test_render_summary_empty():
    assert render_summary([]) == "(no audit events)"


def test_render_summary_single_type():
    events = [_ev("job_success"), _ev("job_success")]
    summary = render_summary(events)
    assert "job_success=2" in summary
    assert "Audit summary:" in summary
