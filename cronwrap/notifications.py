"""High-level notification dispatcher used by the runner."""

from __future__ import annotations

import logging
from typing import Optional

from cronwrap.alerting import AlertConfig, send_email_alert, send_webhook_alert
from cronwrap.executor import ExecutionResult

logger = logging.getLogger(__name__)


def build_alert_subject(job_name: str, result: ExecutionResult) -> str:
    """Return a concise email/webhook subject line."""
    status = "FAILED" if result.returncode != 0 else "OK"
    return f"[cronwrap] {status} — {job_name}"


def build_alert_body(job_name: str, result: ExecutionResult) -> str:
    """Return a human-readable alert body with execution details."""
    lines = [
        f"Job      : {job_name}",
        f"Exit code: {result.returncode}",
        f"Duration : {result.duration:.2f}s",
        "",
    ]
    if result.stdout:
        lines += ["--- stdout ---", result.stdout.strip(), ""]
    if result.stderr:
        lines += ["--- stderr ---", result.stderr.strip(), ""]
    if result.timed_out:
        lines.append("WARNING: job was killed due to timeout.")
    return "\n".join(lines)


def dispatch_alert(
    job_name: str,
    result: ExecutionResult,
    alert_config: Optional[AlertConfig],
    *,
    on_failure_only: bool = True,
) -> None:
    """Send alerts via all configured backends.

    Args:
        job_name: Human-readable name of the cron job.
        result: The ExecutionResult from the last attempt.
        alert_config: AlertConfig instance, or None to skip alerting.
        on_failure_only: When True, suppress alerts for successful runs.
    """
    if alert_config is None:
        return

    failed = result.returncode != 0 or result.timed_out
    if on_failure_only and not failed:
        logger.debug("Job succeeded; skipping alert.")
        return

    subject = build_alert_subject(job_name, result)
    body = build_alert_body(job_name, result)

    if alert_config.to_addresses:
        send_email_alert(alert_config, subject, body)

    if alert_config.webhook_url:
        send_webhook_alert(alert_config, subject, body)
