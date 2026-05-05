"""Hook that records a JobMetric after every run_job execution."""
from __future__ import annotations

import os
from typing import Optional

from cronwrap.executor import ExecutionResult
from cronwrap.history import now_iso
from cronwrap.metrics import JobMetric, append_metric

DEFAULT_METRICS_PATH = os.path.join(".cronwrap", "metrics.json")


def record_metric(
    job_name: str,
    result: ExecutionResult,
    attempt: int = 1,
    metrics_path: Optional[str] = None,
) -> JobMetric:
    """Build a JobMetric from an ExecutionResult and persist it."""
    path = metrics_path or DEFAULT_METRICS_PATH
    metric = JobMetric(
        job_name=job_name,
        timestamp=now_iso(),
        duration_seconds=result.duration_seconds,
        exit_code=result.exit_code if result.exit_code is not None else -1,
        attempt=attempt,
        timed_out=result.timed_out,
        success=result.exit_code == 0 and not result.timed_out,
    )
    append_metric(path, metric)
    return metric
