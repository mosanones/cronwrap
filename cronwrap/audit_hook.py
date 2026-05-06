"""Thin hook called from runner.py to record audit events without coupling."""
from __future__ import annotations

from typing import Optional

from cronwrap.audit import DEFAULT_AUDIT_PATH, append_event, make_event
from cronwrap.executor import ExecutionResult


def record_job_start(job_name: str, command: str, audit_path: str = DEFAULT_AUDIT_PATH) -> None:
    event = make_event(
        event_type="job_start",
        job_name=job_name,
        detail=f"command={command}",
    )
    append_event(event, path=audit_path)


def record_job_end(
    job_name: str,
    result: ExecutionResult,
    audit_path: str = DEFAULT_AUDIT_PATH,
) -> None:
    if result.timed_out:
        event_type = "job_timeout"
    elif result.exit_code == 0:
        event_type = "job_success"
    else:
        event_type = "job_failure"

    event = make_event(
        event_type=event_type,
        job_name=job_name,
        exit_code=result.exit_code,
        duration_seconds=round(result.duration_seconds, 3),
        detail=result.stderr.strip()[:200] if result.stderr else None,
    )
    append_event(event, path=audit_path)


def record_alert_sent(
    job_name: str,
    channel: str,
    audit_path: str = DEFAULT_AUDIT_PATH,
) -> None:
    event = make_event(
        event_type="alert_sent",
        job_name=job_name,
        detail=f"channel={channel}",
    )
    append_event(event, path=audit_path)
