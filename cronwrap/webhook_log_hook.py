"""Hook that ships a run record to a remote webhook after each job execution."""
from __future__ import annotations

import logging
import os
from typing import Optional

from cronwrap.webhook_log import WebhookLogConfig, ship_record

log = logging.getLogger(__name__)

_ENV_URL = "CRONWRAP_WEBHOOK_LOG_URL"
_ENV_TIMEOUT = "CRONWRAP_WEBHOOK_LOG_TIMEOUT"
_ENV_INCLUDE_OUTPUT = "CRONWRAP_WEBHOOK_LOG_INCLUDE_OUTPUT"


def _config_from_env() -> Optional[WebhookLogConfig]:
    """Build a WebhookLogConfig from environment variables, or None if not set."""
    url = os.environ.get(_ENV_URL, "").strip()
    if not url:
        return None
    timeout = int(os.environ.get(_ENV_TIMEOUT, "10"))
    include_output = os.environ.get(_ENV_INCLUDE_OUTPUT, "").lower() in ("1", "true", "yes")
    return WebhookLogConfig(url=url, timeout=timeout, include_output=include_output)


def maybe_ship(record: dict, config: Optional[WebhookLogConfig] = None) -> bool:
    """Ship *record* if a webhook is configured.  Returns True when shipped."""
    cfg = config or _config_from_env()
    if cfg is None:
        return False
    return ship_record(cfg, record)
