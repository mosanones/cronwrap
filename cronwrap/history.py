"""Job execution history tracking — persists run records to a JSON file."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

DEFAULT_HISTORY_PATH = Path(os.environ.get("CRONWRAP_HISTORY_PATH", "/tmp/cronwrap_history.json"))
MAX_HISTORY_ENTRIES = 100


@dataclass
class RunRecord:
    job_name: str
    command: str
    started_at: str          # ISO-8601 UTC
    finished_at: str         # ISO-8601 UTC
    exit_code: int
    duration_seconds: float
    attempts: int
    timed_out: bool
    success: bool

    @staticmethod
    def now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()


def load_history(path: Path = DEFAULT_HISTORY_PATH) -> List[RunRecord]:
    """Return all stored run records, oldest first."""
    if not path.exists():
        return []
    try:
        raw = json.loads(path.read_text())
        return [RunRecord(**entry) for entry in raw]
    except (json.JSONDecodeError, TypeError, KeyError):
        return []


def save_history(records: List[RunRecord], path: Path = DEFAULT_HISTORY_PATH) -> None:
    """Persist records to disk, trimming to MAX_HISTORY_ENTRIES."""
    trimmed = records[-MAX_HISTORY_ENTRIES:]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps([asdict(r) for r in trimmed], indent=2))


def append_record(
    record: RunRecord,
    path: Path = DEFAULT_HISTORY_PATH,
) -> None:
    """Load existing history, append *record*, and save."""
    records = load_history(path)
    records.append(record)
    save_history(records, path)


def last_run(job_name: str, path: Path = DEFAULT_HISTORY_PATH) -> Optional[RunRecord]:
    """Return the most recent record for *job_name*, or None."""
    records = [
        r for r in load_history(path) if r.job_name == job_name
    ]
    return records[-1] if records else None
