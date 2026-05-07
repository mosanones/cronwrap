"""Webhook-based run log shipping: POST job run records to a remote endpoint."""
from __future__ import annotations

import json
import logging
import urllib.request
import urllib.error
from dataclasses import dataclass, field, asdict
from typing import Optional

log = logging.getLogger(__name__)


@dataclass
class WebhookLogConfig:
    url: str
    timeout: int = 10
    headers: dict = field(default_factory=dict)
    include_output: bool = False

    def __post_init__(self) -> None:
        if not self.url.startswith(("http://", "https://")):
            raise ValueError(f"Invalid webhook URL: {self.url!r}")
        if self.timeout < 1:
            raise ValueError("timeout must be >= 1")


def _build_payload(record: dict, include_output: bool) -> dict:
    """Return a JSON-serialisable payload derived from a run record dict."""
    payload = {
        "job": record.get("job_name"),
        "status": record.get("status"),
        "exit_code": record.get("exit_code"),
        "duration": record.get("duration"),
        "started_at": record.get("started_at"),
        "finished_at": record.get("finished_at"),
    }
    if include_output:
        payload["stdout"] = record.get("stdout", "")
        payload["stderr"] = record.get("stderr", "")
    return payload


def ship_record(config: WebhookLogConfig, record: dict) -> bool:
    """POST *record* to the configured webhook.  Returns True on success."""
    payload = _build_payload(record, config.include_output)
    body = json.dumps(payload).encode()
    headers = {"Content-Type": "application/json", **config.headers}
    req = urllib.request.Request(config.url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=config.timeout) as resp:
            status = resp.status
        if status < 300:
            log.debug("webhook_log: shipped record for %s (HTTP %s)", payload["job"], status)
            return True
        log.warning("webhook_log: unexpected HTTP %s for job %s", status, payload["job"])
        return False
    except urllib.error.URLError as exc:
        log.error("webhook_log: failed to ship record: %s", exc)
        return False
