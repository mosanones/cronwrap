"""CLI helpers for displaying throttle status of registered jobs."""
from __future__ import annotations

import datetime
from typing import List

from cronwrap.history import RunRecord, load_history
from cronwrap.throttle import _recent_runs


def _unique_jobs(records: List[RunRecord]) -> List[str]:
    seen: list[str] = []
    for r in records:
        if r.job_name not in seen:
            seen.append(r.job_name)
    return seen


def render_throttle_status(
    history_path: str,
    window_seconds: int = 3600,
    max_runs: int = 10,
) -> str:
    """Return a human-readable throttle status table for all known jobs.

    Args:
        history_path:   Path to the history JSON file.
        window_seconds: Rolling window to count runs in.
        max_runs:       The configured limit (used only for display).

    Returns:
        Multi-line string suitable for printing to a terminal.
    """
    records = load_history(history_path)
    jobs = _unique_jobs(records)
    if not jobs:
        return "No job history found."

    window_label = _fmt_window(window_seconds)
    lines = [
        f"Throttle status  (window: {window_label}, limit: {max_runs} runs)",
        "-" * 55,
        f"{'Job':<35} {'Runs':>6}  {'Status'}",
        "-" * 55,
    ]
    for job in sorted(jobs):
        runs = _recent_runs(records, job, window_seconds)
        status = "OK" if runs < max_runs else "THROTTLED"
        lines.append(f"{job:<35} {runs:>6}  {status}")
    lines.append("-" * 55)
    return "\n".join(lines)


def _fmt_window(seconds: int) -> str:
    if seconds < 120:
        return f"{seconds}s"
    if seconds < 7200:
        return f"{seconds // 60}m"
    return f"{seconds // 3600}h"
