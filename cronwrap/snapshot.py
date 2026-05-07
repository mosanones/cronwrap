"""Job state snapshot: capture and compare successive run outcomes."""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional


@dataclass
class JobSnapshot:
    job_name: str
    last_exit_code: int
    last_status: str          # "success" | "failure" | "timeout"
    last_run_at: str          # ISO-8601
    consecutive_failures: int = 0
    last_duration_seconds: float = 0.0


def _snapshot_path(store_dir: str, job_name: str) -> Path:
    safe = job_name.replace("/", "_").replace(" ", "_")
    return Path(store_dir) / f"{safe}.snapshot.json"


def load_snapshot(store_dir: str, job_name: str) -> Optional[JobSnapshot]:
    path = _snapshot_path(store_dir, job_name)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        return JobSnapshot(**data)
    except Exception:
        return None


def save_snapshot(store_dir: str, snapshot: JobSnapshot) -> None:
    path = _snapshot_path(store_dir, snapshot.job_name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(snapshot), indent=2))


def update_snapshot(
    store_dir: str,
    job_name: str,
    exit_code: int,
    status: str,
    run_at: str,
    duration: float,
) -> JobSnapshot:
    """Load existing snapshot (if any), update fields, persist, and return."""
    prev = load_snapshot(store_dir, job_name)
    consecutive = 0
    if prev is not None and status == "failure":
        consecutive = prev.consecutive_failures + 1
    elif status == "failure":
        consecutive = 1

    snap = JobSnapshot(
        job_name=job_name,
        last_exit_code=exit_code,
        last_status=status,
        last_run_at=run_at,
        consecutive_failures=consecutive,
        last_duration_seconds=duration,
    )
    save_snapshot(store_dir, snap)
    return snap


def state_changed(prev: Optional[JobSnapshot], current: JobSnapshot) -> bool:
    """Return True when the job status differs from the previous snapshot."""
    if prev is None:
        return True
    return prev.last_status != current.last_status
