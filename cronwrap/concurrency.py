"""Concurrency limit enforcement for cron jobs.

Prevents more than N instances of a job from running simultaneously
by tracking active run slots in a lightweight JSON state file.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass
class ConcurrencyConfig:
    max_concurrent: int = 1
    state_dir: str = "/tmp/cronwrap/concurrency"

    def __post_init__(self) -> None:
        if self.max_concurrent < 1:
            raise ValueError("max_concurrent must be >= 1")


class ConcurrencyLimitExceeded(Exception):
    """Raised when the concurrency limit for a job has been reached."""


def _state_path(state_dir: str, job_name: str) -> Path:
    return Path(state_dir) / f"{job_name}.concurrency.json"


def _load_slots(path: Path) -> List[dict]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
        if isinstance(data, list):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return []


def _save_slots(path: Path, slots: List[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(slots, indent=2))


def acquire_slot(job_name: str, config: ConcurrencyConfig, run_id: str) -> None:
    """Acquire a concurrency slot for *job_name*.

    Raises ConcurrencyLimitExceeded if the limit is already reached.
    """
    path = _state_path(config.state_dir, job_name)
    slots = _load_slots(path)
    if len(slots) >= config.max_concurrent:
        raise ConcurrencyLimitExceeded(
            f"Job '{job_name}' already has {len(slots)} active run(s) "
            f"(limit={config.max_concurrent})"
        )
    slots.append({"run_id": run_id, "acquired_at": time.time()})
    _save_slots(path, slots)


def release_slot(job_name: str, config: ConcurrencyConfig, run_id: str) -> None:
    """Release the concurrency slot held by *run_id*."""
    path = _state_path(config.state_dir, job_name)
    slots = _load_slots(path)
    slots = [s for s in slots if s.get("run_id") != run_id]
    _save_slots(path, slots)


def active_slots(job_name: str, config: ConcurrencyConfig) -> List[dict]:
    """Return the list of currently active slot records for *job_name*."""
    path = _state_path(config.state_dir, job_name)
    return _load_slots(path)
