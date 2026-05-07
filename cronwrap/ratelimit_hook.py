"""Integration hook that wires RateLimitConfig into the job runner.

Reads configuration from environment variables so that no code
changes are needed to enable rate limiting for an existing job.

Environment variables
---------------------
CRONWRAP_RATELIMIT_MAX_RUNS      – int, max executions in window
CRONWRAP_RATELIMIT_WINDOW_SECONDS – int, window length in seconds
CRONWRAP_RATELIMIT_STORE_DIR     – optional path for state files
                                    (default: .cronwrap/ratelimit)
"""
from __future__ import annotations

import os

from cronwrap.ratelimit import (
    RateLimitConfig,
    RateLimitExceeded,
    check_rate_limit,
)

_DEFAULT_STORE = ".cronwrap/ratelimit"


def _config_from_env() -> RateLimitConfig | None:
    """Return a RateLimitConfig built from env-vars, or None if not set."""
    max_runs_raw = os.environ.get("CRONWRAP_RATELIMIT_MAX_RUNS")
    window_raw = os.environ.get("CRONWRAP_RATELIMIT_WINDOW_SECONDS")

    if max_runs_raw is None or window_raw is None:
        return None

    try:
        return RateLimitConfig(
            max_runs=int(max_runs_raw),
            window_seconds=int(window_raw),
        )
    except (ValueError, TypeError):
        return None


def maybe_check_rate_limit(job_name: str) -> None:
    """Enforce the rate limit for *job_name* if env-vars are configured.

    Raises RateLimitExceeded (a subclass of Exception) when the limit
    is breached so the caller can decide how to surface the error.
    Does nothing when the required env-vars are absent.
    """
    config = _config_from_env()
    if config is None:
        return

    store_dir = os.environ.get("CRONWRAP_RATELIMIT_STORE_DIR", _DEFAULT_STORE)
    check_rate_limit(job_name, config, store_dir=store_dir)
