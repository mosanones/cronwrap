"""CLI helpers for displaying heartbeat status."""
from __future__ import annotations

import datetime
from typing import Iterable

from cronwrap.heartbeat import HeartbeatRecord, load_heartbeats, check_missed


def _age_str(last_ping: str) -> str:
    """Human-readable age of a heartbeat ping."""
    now = datetime.datetime.now(datetime.timezone.utc)
    last = datetime.datetime.fromisoformat(last_ping)
    if last.tzinfo is None:
        last = last.replace(tzinfo=datetime.timezone.utc)
    secs = int((now - last).total_seconds())
    if secs < 60:
        return f"{secs}s ago"
    if secs < 3600:
        return f"{secs // 60}m ago"
    return f"{secs // 3600}h ago"


def render_heartbeat(record: HeartbeatRecord) -> str:
    icon = "💔" if record.missed else "💚"
    return (
        f"{icon} {record.job_name:<30} "
        f"last={_age_str(record.last_ping):<12} "
        f"interval={record.interval_seconds}s"
    )


def render_all_heartbeats(store_dir: str) -> str:
    records = load_heartbeats(store_dir)
    if not records:
        return "No heartbeat records found."
    # Refresh missed flags before rendering
    check_missed(store_dir)
    records = load_heartbeats(store_dir)
    lines = [render_heartbeat(r) for r in sorted(records.values(), key=lambda r: r.job_name)]
    return "\n".join(lines)


def render_missed_heartbeats(store_dir: str) -> str:
    missed = check_missed(store_dir)
    if not missed:
        return "All heartbeats are on time."
    lines = [render_heartbeat(r) for r in sorted(missed, key=lambda r: r.job_name)]
    return "MISSED HEARTBEATS:\n" + "\n".join(lines)
