"""Thin integration layer: wire throttle checking into the job runner."""
from __future__ import annotations

from cronwrap.throttle import ThrottleConfig, ThrottleExceeded, check_throttle


def maybe_throttle(
    job_name: str,
    history_path: str,
    max_runs: int | None = None,
    window_seconds: int | None = None,
) -> None:
    """Check the throttle for *job_name* when both parameters are supplied.

    Does nothing when either *max_runs* or *window_seconds* is ``None``.

    Raises:
        ThrottleExceeded: propagated from :func:`check_throttle`.
    """
    if max_runs is None or window_seconds is None:
        return
    cfg = ThrottleConfig(max_runs=max_runs, window_seconds=window_seconds)
    check_throttle(job_name, cfg, history_path)


__all__ = ["maybe_throttle", "ThrottleExceeded"]
