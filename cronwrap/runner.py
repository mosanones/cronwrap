"""High-level runner that wires together config, retry, and alerting."""

import logging
import sys
from typing import Optional

from cronwrap.config import JobConfig
from cronwrap.executor import ExecutionResult
from cronwrap.retry import run_with_retry

logger = logging.getLogger(__name__)


def _setup_logging(config: JobConfig) -> None:
    handlers = [logging.StreamHandler(sys.stdout)]
    if config.log_file:
        handlers.append(logging.FileHandler(config.log_file))
    logging.basicConfig(
        level=getattr(logging, config.log_level.upper()),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=handlers,
    )


def _maybe_alert(config: JobConfig, result: ExecutionResult) -> None:
    """Placeholder alerting hook — replace with real email/webhook logic."""
    should_alert = (not result.success and config.alert_on_failure) or (
        result.success and config.alert_on_success
    )
    if not should_alert or not config.alert_emails:
        return

    status = "SUCCEEDED" if result.success else "FAILED"
    logger.info(
        "[ALERT] Job '%s' %s (exit=%d). Would notify: %s",
        config.name,
        status,
        result.exit_code,
        ", ".join(config.alert_emails),
    )


def run_job(config: JobConfig) -> ExecutionResult:
    """
    Execute a cron job according to the provided JobConfig.

    Returns the final ExecutionResult.
    """
    config.validate()
    _setup_logging(config)

    logger.info("Starting job '%s': %s", config.name, config.command)

    result = run_with_retry(
        command=config.command,
        retries=config.retries,
        delay=config.retry_delay,
        backoff=config.retry_backoff,
        timeout=config.timeout,
        on_retry=lambda r: logger.warning(
            "Attempt %d failed (exit=%d): %s", r.attempt, r.exit_code, r.stderr
        ),
    )

    _maybe_alert(config, result)

    logger.info(
        "Job '%s' finished — success=%s, attempts=%d, duration=%.3fs",
        config.name,
        result.success,
        result.attempt,
        result.duration_seconds,
    )
    return result
