"""High-level job runner — orchestrates config, retry, alerting, and history."""

from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone

from cronwrap.config import JobConfig
from cronwrap.executor import ExecutionResult
from cronwrap.history import RunRecord, append_record
from cronwrap.notifications import dispatch_alert
from cronwrap.retry import run_with_retry


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        stream=sys.stdout,
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )


def _maybe_alert(cfg: JobConfig, result: ExecutionResult, attempts: int) -> None:
    """Send an alert when the job failed and alerting is configured."""
    if result.success:
        return
    if cfg.alert is None:
        return
    dispatch_alert(cfg, result, attempts)


def _build_record(
    cfg: JobConfig,
    result: ExecutionResult,
    started_at: str,
    finished_at: str,
    attempts: int,
) -> RunRecord:
    return RunRecord(
        job_name=cfg.name,
        command=cfg.command,
        started_at=started_at,
        finished_at=finished_at,
        exit_code=result.exit_code if result.exit_code is not None else -1,
        duration_seconds=result.duration_seconds,
        attempts=attempts,
        timed_out=result.timed_out,
        success=result.success,
    )


def run_job(cfg: JobConfig, verbose: bool = False) -> ExecutionResult:
    """Execute the job described by *cfg*, record history, and alert on failure."""
    _setup_logging(verbose)
    log = logging.getLogger(__name__)

    log.info("Starting job '%s': %s", cfg.name, cfg.command)
    started_at = datetime.now(timezone.utc).isoformat()

    result, attempts = run_with_retry(cfg)

    finished_at = datetime.now(timezone.utc).isoformat()

    status = "succeeded" if result.success else ("timed out" if result.timed_out else "failed")
    log.info(
        "Job '%s' %s after %d attempt(s) in %.2fs (exit_code=%s)",
        cfg.name, status, attempts, result.duration_seconds, result.exit_code,
    )
    if result.stdout:
        log.debug("stdout:\n%s", result.stdout)
    if result.stderr:
        log.debug("stderr:\n%s", result.stderr)

    record = _build_record(cfg, result, started_at, finished_at, attempts)
    append_record(record)

    _maybe_alert(cfg, result, attempts)

    return result
