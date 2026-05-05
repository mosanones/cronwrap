"""Alerting backends for cronwrap job notifications."""

from __future__ import annotations

import logging
import smtplib
from dataclasses import dataclass, field
from email.message import EmailMessage
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class AlertConfig:
    """Configuration for alert delivery."""

    smtp_host: str = "localhost"
    smtp_port: int = 25
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    use_tls: bool = False
    from_address: str = "cronwrap@localhost"
    to_addresses: list[str] = field(default_factory=list)
    webhook_url: Optional[str] = None


def send_email_alert(
    config: AlertConfig,
    subject: str,
    body: str,
) -> bool:
    """Send an alert email via SMTP. Returns True on success."""
    if not config.to_addresses:
        logger.warning("No to_addresses configured; skipping email alert.")
        return False

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = config.from_address
    msg["To"] = ", ".join(config.to_addresses)
    msg.set_content(body)

    try:
        cls = smtplib.SMTP_SSL if config.use_tls else smtplib.SMTP
        with cls(config.smtp_host, config.smtp_port) as smtp:
            if config.smtp_user and config.smtp_password:
                smtp.login(config.smtp_user, config.smtp_password)
            smtp.send_message(msg)
        logger.info("Alert email sent to %s", config.to_addresses)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to send alert email: %s", exc)
        return False


def send_webhook_alert(
    config: AlertConfig,
    subject: str,
    body: str,
) -> bool:
    """POST a JSON alert payload to a webhook URL. Returns True on success."""
    if not config.webhook_url:
        logger.warning("No webhook_url configured; skipping webhook alert.")
        return False

    try:
        import urllib.request, json  # noqa: E401

        payload = json.dumps({"subject": subject, "body": body}).encode()
        req = urllib.request.Request(
            config.webhook_url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            status = resp.status
        logger.info("Webhook alert delivered (HTTP %s)", status)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to deliver webhook alert: %s", exc)
        return False
