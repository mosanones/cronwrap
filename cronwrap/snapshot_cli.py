"""CLI rendering helpers for job snapshots."""
from __future__ import annotations

from pathlib import Path
from typing import List

from cronwrap.snapshot import JobSnapshot, load_snapshot, _snapshot_path


_STATUS_ICON = {
    "success": "✅",
    "failure": "❌",
    "timeout": "⏱️",
}


def render_snapshot(snap: JobSnapshot) -> str:
    icon = _STATUS_ICON.get(snap.last_status, "❓")
    lines = [
        f"{icon}  {snap.job_name}",
        f"   status   : {snap.last_status}",
        f"   exit code: {snap.last_exit_code}",
        f"   last run : {snap.last_run_at}",
        f"   duration : {snap.last_duration_seconds:.2f}s",
        f"   consec.  : {snap.consecutive_failures} failure(s)",
    ]
    return "\n".join(lines)


def render_all_snapshots(store_dir: str) -> str:
    directory = Path(store_dir)
    if not directory.exists():
        return "(no snapshots found)"

    files = sorted(directory.glob("*.snapshot.json"))
    if not files:
        return "(no snapshots found)"

    parts: List[str] = []
    for f in files:
        job_name = f.stem.replace(".snapshot", "")
        snap = load_snapshot(store_dir, job_name)
        if snap:
            parts.append(render_snapshot(snap))
    return "\n\n".join(parts)


def render_flapping_jobs(store_dir: str, threshold: int = 2) -> str:
    """List jobs with consecutive_failures >= threshold."""
    directory = Path(store_dir)
    if not directory.exists():
        return "(no snapshots found)"

    lines = [f"Jobs with >= {threshold} consecutive failure(s):"]
    found = False
    for f in sorted(directory.glob("*.snapshot.json")):
        job_name = f.stem.replace(".snapshot", "")
        snap = load_snapshot(store_dir, job_name)
        if snap and snap.consecutive_failures >= threshold:
            lines.append(f"  ❌ {snap.job_name}  ({snap.consecutive_failures} failures)")
            found = True
    if not found:
        lines.append("  (none)")
    return "\n".join(lines)
