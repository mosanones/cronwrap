"""Hook that enforces quota limits before a job runs."""
from __future__ import annotations

import os

from cronwrap.quota import QuotaConfig, QuotaExceeded, check_quota


def _config_from_env() -> QuotaConfig | None:
    """Build a QuotaConfig from environment variables, or return None.

    Environment variables:
        CRONWRAP_QUOTA_MAX_RUNS  – integer, required to enable quota
        CRONWRAP_QUOTA_PERIOD    – hourly | daily | weekly | monthly (default: daily)
    """
    raw_max = os.environ.get("CRONWRAP_QUOTA_MAX_RUNS")
    if not raw_max:
        return None
    try:
        max_runs = int(raw_max)
    except ValueError:
        return None
    period = os.environ.get("CRONWRAP_QUOTA_PERIOD", "daily")
    try:
        return QuotaConfig(max_runs=max_runs, period=period)
    except ValueError:
        return None


def maybe_check_quota(job_name: str, base_dir: str | None = None) -> None:
    """If quota env-vars are set, check the quota and raise QuotaExceeded if exhausted.

    This function is intended to be called at the start of a job run, before
    the command is executed.
    """
    config = _config_from_env()
    if config is None:
        return
    check_quota(job_name, config, base_dir=base_dir)
