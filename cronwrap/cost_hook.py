"""Hook that records a cost entry after each job run."""
from __future__ import annotations

import os
from cronwrap.cost import CostEntry, append_cost_entry
from cronwrap.executor import ExecutionResult

_DEFAULT_COST_PER_SECOND = 0.000010  # USD


def record_cost(
    job_name: str,
    result: ExecutionResult,
    store_dir: str,
    cost_per_second: float | None = None,
    currency: str = "USD",
) -> None:
    """Append a cost entry for the completed run."""
    if result.duration is None:
        return

    rate = cost_per_second
    if rate is None:
        env_rate = os.environ.get("CRONWRAP_COST_PER_SECOND")
        rate = float(env_rate) if env_rate else _DEFAULT_COST_PER_SECOND

    entry = CostEntry(
        job_name=job_name,
        timestamp=result.started_at or "",
        duration_seconds=result.duration,
        cost_per_second=rate,
        currency=currency,
    )
    append_cost_entry(store_dir, entry)
