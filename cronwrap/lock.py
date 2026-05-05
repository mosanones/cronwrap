"""File-based locking to prevent overlapping cron job executions."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

DEFAULT_LOCK_DIR = Path("/tmp/cronwrap/locks")


@dataclass
class LockInfo:
    job_name: str
    pid: int
    acquired_at: float

    def age_seconds(self) -> float:
        return time.time() - self.acquired_at


class LockError(Exception):
    """Raised when a lock cannot be acquired."""


def _lock_path(job_name: str, lock_dir: Path) -> Path:
    safe_name = job_name.replace("/", "_").replace(" ", "_")
    return lock_dir / f"{safe_name}.lock"


def acquire_lock(
    job_name: str,
    lock_dir: Path = DEFAULT_LOCK_DIR,
    stale_after: Optional[float] = None,
) -> Path:
    """Acquire a lock for *job_name*.

    Returns the lock file path on success.
    Raises LockError if the lock is already held (and not stale).
    """
    lock_dir.mkdir(parents=True, exist_ok=True)
    path = _lock_path(job_name, lock_dir)

    if path.exists():
        try:
            parts = path.read_text().strip().split(",")
            pid = int(parts[0])
            acquired_at = float(parts[1])
            age = time.time() - acquired_at
            if stale_after is not None and age > stale_after:
                path.unlink(missing_ok=True)
            else:
                raise LockError(
                    f"Job '{job_name}' is already running (pid={pid}, age={age:.1f}s)"
                )
        except (ValueError, IndexError):
            # Corrupt lock file — remove it
            path.unlink(missing_ok=True)

    path.write_text(f"{os.getpid()},{time.time()}")
    return path


def release_lock(lock_path: Path) -> None:
    """Release a previously acquired lock."""
    lock_path.unlink(missing_ok=True)


def read_lock_info(job_name: str, lock_dir: Path = DEFAULT_LOCK_DIR) -> Optional[LockInfo]:
    """Return LockInfo if a lock file exists, otherwise None."""
    path = _lock_path(job_name, lock_dir)
    if not path.exists():
        return None
    try:
        parts = path.read_text().strip().split(",")
        return LockInfo(job_name=job_name, pid=int(parts[0]), acquired_at=float(parts[1]))
    except (ValueError, IndexError):
        return None
