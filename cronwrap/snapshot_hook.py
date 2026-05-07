"""Hook that records a snapshot after each job run and detects state changes."""
from __future__ import annotations

import os
from typing import Optional

from cronwrap.snapshot import JobSnapshot, load_snapshot, update_snapshot, state_changed
from cronwrap.executor import ExecutionResult

_DEFAULT_STORE = os.environ.get("CRONWRAP_SNAPSHOT_DIR", ".cronwrap/snapshots")


def record_snapshot(
    job_name: str,
    result: ExecutionResult,
    run_at: str,
    store_dir: str = _DEFAULT_STORE,
) -> tuple[JobSnapshot, bool]:
    """Persist a snapshot and return ``(snapshot, changed)``.

    *changed* is ``True`` when the job's status flipped since the last run
    (e.g. failure → success or success → failure).
    """
    prev = load_snapshot(store_dir, job_name)

    if result.timed_out:
        status = "timeout"
    elif result.exit_code == 0:
        status = "success"
    else:
        status = "failure"

    snap = update_snapshot(
        store_dir=store_dir,
        job_name=job_name,
        exit_code=result.exit_code,
        status=status,
        run_at=run_at,
        duration=result.duration_seconds,
    )
    changed = state_changed(prev, snap)
    return snap, changed
