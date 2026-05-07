"""Hook that fires a heartbeat ping after a successful job run."""
from __future__ import annotations

import os
from typing import Optional

from cronwrap.heartbeat import ping, HeartbeatRecord

_DEFAULT_STORE = os.path.join(os.path.expanduser("~"), ".cronwrap")


def maybe_ping(
    job_name: str,
    succeeded: bool,
    store_dir: Optional[str] = None,
    interval_seconds: Optional[int] = None,
) -> Optional[HeartbeatRecord]:
    """Ping the heartbeat store if the job succeeded and an interval is configured.

    *interval_seconds* can also be supplied via the environment variable
    ``CRONWRAP_HEARTBEAT_INTERVAL`` (integer seconds).
    """
    if not succeeded:
        return None

    env_interval = os.environ.get("CRONWRAP_HEARTBEAT_INTERVAL")
    effective_interval = interval_seconds
    if effective_interval is None and env_interval:
        try:
            effective_interval = int(env_interval)
        except ValueError:
            return None

    if effective_interval is None or effective_interval <= 0:
        return None

    effective_store = store_dir or os.environ.get("CRONWRAP_STORE_DIR", _DEFAULT_STORE)
    return ping(effective_store, job_name, effective_interval)
