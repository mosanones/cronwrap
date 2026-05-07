"""Hook that integrates the circuit breaker with the job runner."""
from __future__ import annotations

import os
import time
from datetime import datetime, timezone

from cronwrap.circuit_breaker import (
    CircuitBreakerConfig,
    CircuitOpen,
    check_circuit,
    record_outcome,
)
from cronwrap.executor import ExecutionResult

_DEFAULT_STORE = os.path.join(
    os.environ.get("CRONWRAP_DATA_DIR", ".cronwrap"), "circuit"
)


def _config_from_env() -> CircuitBreakerConfig:
    max_failures = int(os.environ.get("CRONWRAP_CB_MAX_FAILURES", "3"))
    reset_after = int(os.environ.get("CRONWRAP_CB_RESET_AFTER", "300"))
    return CircuitBreakerConfig(max_failures=max_failures, reset_after=reset_after)


def maybe_check(
    job_name: str,
    store_dir: str = _DEFAULT_STORE,
    cfg: CircuitBreakerConfig | None = None,
) -> None:
    """Call before running a job; raises CircuitOpen if the circuit is open."""
    if cfg is None:
        cfg = _config_from_env()
    check_circuit(store_dir, job_name, cfg, time.time())


def maybe_record(
    job_name: str,
    result: ExecutionResult,
    store_dir: str = _DEFAULT_STORE,
    cfg: CircuitBreakerConfig | None = None,
) -> None:
    """Call after a job completes to update circuit state."""
    if cfg is None:
        cfg = _config_from_env()
    now_iso = datetime.now(timezone.utc).isoformat()
    record_outcome(
        store_dir,
        job_name,
        success=(result.exit_code == 0),
        cfg=cfg,
        now_iso=now_iso,
    )
