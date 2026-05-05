"""Context manager and decorator for cronwrap job locking."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from cronwrap.lock import DEFAULT_LOCK_DIR, LockError, acquire_lock, release_lock


class JobLock:
    """Context manager that holds a file lock for the duration of a block.

    Example::

        with JobLock("my-job") as lock:
            run_my_job()
    """

    def __init__(
        self,
        job_name: str,
        lock_dir: Path = DEFAULT_LOCK_DIR,
        stale_after: Optional[float] = None,
        skip_if_locked: bool = False,
    ) -> None:
        self.job_name = job_name
        self.lock_dir = lock_dir
        self.stale_after = stale_after
        self.skip_if_locked = skip_if_locked
        self._lock_path: Optional[Path] = None
        self.skipped: bool = False

    def __enter__(self) -> "JobLock":
        try:
            self._lock_path = acquire_lock(
                self.job_name,
                lock_dir=self.lock_dir,
                stale_after=self.stale_after,
            )
        except LockError:
            if self.skip_if_locked:
                self.skipped = True
            else:
                raise
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if self._lock_path is not None:
            release_lock(self._lock_path)
        # Do not suppress exceptions
        return False
