"""Retry logic for failed cron job executions."""

import logging
import time
from typing import Callable, Optional

from cronwrap.executor import ExecutionResult, run_command

logger = logging.getLogger(__name__)


def run_with_retry(
    command: str,
    retries: int = 3,
    delay: float = 5.0,
    backoff: float = 2.0,
    timeout: Optional[int] = None,
    on_retry: Optional[Callable[[ExecutionResult], None]] = None,
) -> ExecutionResult:
    """
    Run a command with configurable retry logic.

    Args:
        command:  Shell command to execute.
        retries:  Maximum number of attempts (including the first).
        delay:    Initial delay in seconds between retries.
        backoff:  Multiplier applied to delay after each failure.
        timeout:  Per-attempt timeout in seconds.
        on_retry: Optional callback invoked after each failed attempt.

    Returns:
        The final ExecutionResult (success or last failure).
    """
    if retries < 1:
        raise ValueError("retries must be >= 1")

    current_delay = delay
    result: ExecutionResult

    for attempt in range(1, retries + 1):
        result = run_command(command, timeout=timeout, attempt=attempt)

        if result.success:
            return result

        if on_retry:
            on_retry(result)

        if attempt < retries:
            logger.info(
                "Retrying in %.1f seconds (attempt %d/%d)…",
                current_delay,
                attempt,
                retries,
            )
            time.sleep(current_delay)
            current_delay *= backoff
        else:
            logger.error("All %d attempts failed for command: %s", retries, command)

    return result
