"""Rate-limit enforcement for cron jobs.

Allows capping the number of executions of a job within a rolling
time window, independently of the throttle module (which is
history-based).  This module operates on a lightweight counter file
so it is fast and has no dependency on the full run history.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass
class RateLimitConfig:
    max_runs: int          # maximum executions allowed in the window
    window_seconds: int    # rolling window length in seconds

    def __post_init__(self) -> None:
        if self.max_runs < 1:
            raise ValueError("max_runs must be >= 1")
        if self.window_seconds < 1:
            raise ValueError("window_seconds must be >= 1")


class RateLimitExceeded(Exception):
    """Raised when the rate limit for a job has been reached."""


@dataclass
class _RateLimitState:
    timestamps: List[float] = field(default_factory=list)


def _state_path(store_dir: str, job_name: str) -> Path:
    safe = job_name.replace(os.sep, "_").replace(" ", "_")
    return Path(store_dir) / f"{safe}.ratelimit.json"


def _load_state(path: Path) -> _RateLimitState:
    try:
        data = json.loads(path.read_text())
        return _RateLimitState(timestamps=data.get("timestamps", []))
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return _RateLimitState()


def _save_state(path: Path, state: _RateLimitState) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"timestamps": state.timestamps}))


def check_rate_limit(
    job_name: str,
    config: RateLimitConfig,
    store_dir: str = ".cronwrap/ratelimit",
    *,
    _now: float | None = None,
) -> None:
    """Check and record an execution attempt.

    Raises RateLimitExceeded if the job has already been run
    *max_runs* times within the last *window_seconds* seconds.
    On success the current timestamp is persisted so future calls
    can account for this execution.
    """
    now = _now if _now is not None else time.time()
    cutoff = now - config.window_seconds

    path = _state_path(store_dir, job_name)
    state = _load_state(path)

    # Prune timestamps outside the current window
    state.timestamps = [t for t in state.timestamps if t > cutoff]

    if len(state.timestamps) >= config.max_runs:
        raise RateLimitExceeded(
            f"Job '{job_name}' has reached {config.max_runs} runs "
            f"within the last {config.window_seconds}s window."
        )

    state.timestamps.append(now)
    _save_state(path, state)
