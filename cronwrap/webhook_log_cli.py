"""CLI helpers for testing / previewing the webhook log feature."""
from __future__ import annotations

import json
from typing import List

from cronwrap.webhook_log import WebhookLogConfig, _build_payload


def render_payload_preview(record: dict, include_output: bool = False) -> str:
    """Return a pretty-printed JSON preview of the payload that would be shipped."""
    payload = _build_payload(record, include_output)
    return json.dumps(payload, indent=2)


def render_config(config: WebhookLogConfig) -> str:
    """Return a human-readable summary of the webhook log configuration."""
    lines: List[str] = [
        f"URL             : {config.url}",
        f"Timeout (s)     : {config.timeout}",
        f"Include output  : {config.include_output}",
    ]
    if config.headers:
        lines.append("Custom headers  :")
        for k, v in config.headers.items():
            lines.append(f"  {k}: {v}")
    else:
        lines.append("Custom headers  : (none)")
    return "\n".join(lines)
