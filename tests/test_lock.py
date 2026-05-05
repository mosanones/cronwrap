"""Tests for cronwrap.lock and cronwrap.lock_context."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from cronwrap.lock import LockError, acquire_lock, read_lock_info, release_lock
from cronwrap.lock_context import JobLock


@pytest.fixture()
def lock_dir(tmp_path: Path) -> Path:
    return tmp_path / "locks"


def test_acquire_creates_lock_file(lock_dir: Path) -> None:
    path = acquire_lock("test-job", lock_dir=lock_dir)
    assert path.exists()
    release_lock(path)


def test_double_acquire_raises(lock_dir: Path) -> None:
    path = acquire_lock("test-job", lock_dir=lock_dir)
    try:
        with pytest.raises(LockError, match="already running"):
            acquire_lock("test-job", lock_dir=lock_dir)
    finally:
        release_lock(path)


def test_release_removes_file(lock_dir: Path) -> None:
    path = acquire_lock("test-job", lock_dir=lock_dir)
    release_lock(path)
    assert not path.exists()


def test_stale_lock_is_replaced(lock_dir: Path) -> None:
    path = acquire_lock("test-job", lock_dir=lock_dir)
    # Backdate the lock file
    path.write_text(f"9999,{time.time() - 9999}")
    new_path = acquire_lock("test-job", lock_dir=lock_dir, stale_after=60.0)
    assert new_path.exists()
    release_lock(new_path)


def test_corrupt_lock_file_is_replaced(lock_dir: Path) -> None:
    lock_dir.mkdir(parents=True, exist_ok=True)
    corrupt = lock_dir / "test-job.lock"
    corrupt.write_text("not-valid-data")
    path = acquire_lock("test-job", lock_dir=lock_dir)
    assert path.exists()
    release_lock(path)


def test_read_lock_info_returns_none_when_no_lock(lock_dir: Path) -> None:
    info = read_lock_info("missing-job", lock_dir=lock_dir)
    assert info is None


def test_read_lock_info_returns_data(lock_dir: Path) -> None:
    path = acquire_lock("info-job", lock_dir=lock_dir)
    info = read_lock_info("info-job", lock_dir=lock_dir)
    assert info is not None
    assert info.job_name == "info-job"
    assert info.pid > 0
    assert info.age_seconds() >= 0.0
    release_lock(path)


def test_job_lock_context_manager(lock_dir: Path) -> None:
    with JobLock("ctx-job", lock_dir=lock_dir) as lock:
        assert lock._lock_path is not None and lock._lock_path.exists()
        assert not lock.skipped
    assert not lock._lock_path.exists()


def test_job_lock_raises_on_conflict(lock_dir: Path) -> None:
    with JobLock("conflict-job", lock_dir=lock_dir):
        with pytest.raises(LockError):
            with JobLock("conflict-job", lock_dir=lock_dir):
                pass


def test_job_lock_skip_if_locked(lock_dir: Path) -> None:
    with JobLock("skip-job", lock_dir=lock_dir):
        with JobLock("skip-job", lock_dir=lock_dir, skip_if_locked=True) as inner:
            assert inner.skipped
