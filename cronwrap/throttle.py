"""Rate-limiting / throttle guard for cron jobs.

Prevents a job from running more than `max_runs` times within a
rolling `window_seconds` interval by inspecting the run history.
"""
from __future__ import annotations

import dataclasses
from typing import List

from cronwrap.history import RunRecord, load_history


@dataclasses.dataclass
class ThrottleConfig:
    max_runs: int        # maximum executions allowed in the window
    window_seconds: int  # rolling window length in seconds

    def __post_init__(self) -> None:
        if self.max_runs < 1:
            raise ValueError("max_runs must be >= 1")
        if self.window_seconds < 1:
            raise ValueError("window_seconds must be >= 1")


class ThrottleExceeded(Exception:
    """Raised when a job has exceeded its allowed run rate."""

    def __init__(self, job_name: str, runs: int, window: int) -> None:
        self.job_name = job_name
        self.runs = runs
        self.window = window
        super().__init__(
            f"Job '{job_name}' has run {runs} time(s) in the last "
            f"{window}s — throttle limit reached."
        )


def _recent_runs(records: List[RunRecord], job_name: str, window_seconds: int) -> int:
    """Count how many records for *job_name* fall within *window_seconds* of the
    most recent record's timestamp (or wall-clock now if no records exist)."""
    import datetime

    now = datetime.datetime.now(datetime.timezone.utc)
    cutoff = now - datetime.timedelta(seconds=window_seconds)
    count = 0
    for rec in records:
        if rec.job_name != job_name:
            continue
        try:
            ts = datetime.datetime.fromisoformat(rec.started_at)
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=datetime.timezone.utc)
        except (ValueError, AttributeError):
            continue
        if ts >= cutoff:
            count += 1
    return count


def check_throttle(
    job_name: str,
    config: ThrottleConfig,
    history_path: str,
) -> None:
    """Raise :class:`ThrottleExceeded` if the job is over its rate limit.

    Args:
        job_name:     Identifier for the job (matches RunRecord.job_name).
        config:       Throttle parameters.
        history_path: Path to the JSON history file.
    """
    records = load_history(history_path)
    runs = _recent_runs(records, job_name, config.window_seconds)
    if runs >= config.max_runs:
        raise ThrottleExceeded(job_name, runs, config.window_seconds)
