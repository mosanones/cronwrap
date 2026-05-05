"""Core executor module for running wrapped cron jobs."""

import subprocess
import time
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    command: str
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    attempt: int
    success: bool = field(init=False)

    def __post_init__(self):
        self.success = self.exit_code == 0


def run_command(
    command: str,
    timeout: Optional[int] = None,
    attempt: int = 1,
) -> ExecutionResult:
    """Execute a shell command and return a structured result."""
    logger.info("Running command (attempt %d): %s", attempt, command)
    start = time.monotonic()

    try:
        proc = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        duration = time.monotonic() - start
        result = ExecutionResult(
            command=command,
            exit_code=proc.returncode,
            stdout=proc.stdout.strip(),
            stderr=proc.stderr.strip(),
            duration_seconds=round(duration, 3),
            attempt=attempt,
        )
    except subprocess.TimeoutExpired:
        duration = time.monotonic() - start
        logger.error("Command timed out after %s seconds", timeout)
        result = ExecutionResult(
            command=command,
            exit_code=-1,
            stdout="",
            stderr=f"Command timed out after {timeout} seconds",
            duration_seconds=round(duration, 3),
            attempt=attempt,
        )

    if result.success:
        logger.info("Command succeeded in %.3fs", result.duration_seconds)
    else:
        logger.warning(
            "Command failed (exit %d) in %.3fs", result.exit_code, result.duration_seconds
        )

    return result
