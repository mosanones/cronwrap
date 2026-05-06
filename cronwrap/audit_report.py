"""Simple text renderer for audit log entries."""
from __future__ import annotations

from typing import List

from cronwrap.audit import AuditEvent

_ICONS = {
    "job_start": "▶",
    "job_success": "✓",
    "job_failure": "✗",
    "job_timeout": "⏱",
    "alert_sent": "✉",
}


def _icon(event_type: str) -> str:
    return _ICONS.get(event_type, "•")


def render_event(event: AuditEvent) -> str:
    """Return a single human-readable line for one audit event."""
    parts = [
        f"{event.timestamp}",
        f"{_icon(event.event_type)} [{event.event_type}]",
        event.job_name,
    ]
    if event.exit_code is not None:
        parts.append(f"exit={event.exit_code}")
    if event.duration_seconds is not None:
        parts.append(f"{event.duration_seconds:.3f}s")
    if event.detail:
        parts.append(f"({event.detail})")
    return "  ".join(parts)


def render_events(events: List[AuditEvent]) -> str:
    """Render a list of audit events as a multi-line string."""
    if not events:
        return "(no audit events)"
    return "\n".join(render_event(e) for e in events)


def render_summary(events: List[AuditEvent]) -> str:
    """Render a short summary line: counts per event type."""
    counts: dict = {}
    for e in events:
        counts[e.event_type] = counts.get(e.event_type, 0) + 1
    if not counts:
        return "(no audit events)"
    parts = [f"{k}={v}" for k, v in sorted(counts.items())]
    return "Audit summary: " + ", ".join(parts)
