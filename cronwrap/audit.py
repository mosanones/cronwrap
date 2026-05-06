"""Audit log — append-only record of significant cronwrap events."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import List, Optional

DEFAULT_AUDIT_PATH = os.path.join(os.path.expanduser("~"), ".cronwrap", "audit.jsonl")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class AuditEvent:
    timestamp: str
    event_type: str   # e.g. "job_start", "job_success", "job_failure", "lock_acquired", "alert_sent"
    job_name: str
    detail: Optional[str] = None
    exit_code: Optional[int] = None
    duration_seconds: Optional[float] = None


def append_event(
    event: AuditEvent,
    path: str = DEFAULT_AUDIT_PATH,
) -> None:
    """Append a single audit event as a JSON line."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(asdict(event)) + "\n")


def load_events(
    path: str = DEFAULT_AUDIT_PATH,
    job_name: Optional[str] = None,
    event_type: Optional[str] = None,
    limit: int = 200,
) -> List[AuditEvent]:
    """Load audit events, optionally filtering by job name and/or event type."""
    if not os.path.exists(path):
        return []
    events: List[AuditEvent] = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                events.append(AuditEvent(**data))
            except (json.JSONDecodeError, TypeError):
                continue
    if job_name:
        events = [e for e in events if e.job_name == job_name]
    if event_type:
        events = [e for e in events if e.event_type == event_type]
    return events[-limit:]


def make_event(
    event_type: str,
    job_name: str,
    detail: Optional[str] = None,
    exit_code: Optional[int] = None,
    duration_seconds: Optional[float] = None,
) -> AuditEvent:
    """Convenience constructor that stamps the current UTC time."""
    return AuditEvent(
        timestamp=_now_iso(),
        event_type=event_type,
        job_name=job_name,
        detail=detail,
        exit_code=exit_code,
        duration_seconds=duration_seconds,
    )
