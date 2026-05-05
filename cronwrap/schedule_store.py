"""Persist and query scheduled job metadata (next-run times, enabled flag)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

DEFAULT_STORE = Path("~/.cronwrap/schedule.json").expanduser()


@dataclass
class ScheduleEntry:
    job_name: str
    cron_expression: str
    enabled: bool = True
    last_run: Optional[str] = None   # ISO-8601
    next_run: Optional[str] = None   # ISO-8601


def load_store(path: Path = DEFAULT_STORE) -> dict[str, ScheduleEntry]:
    """Load all schedule entries from *path*. Returns empty dict if missing."""
    if not path.exists():
        return {}
    try:
        raw: list[dict] = json.loads(path.read_text())
    except (json.JSONDecodeError, ValueError):
        return {}
    return {d["job_name"]: ScheduleEntry(**d) for d in raw}


def save_store(
    entries: dict[str, ScheduleEntry], path: Path = DEFAULT_STORE
) -> None:
    """Persist *entries* to *path*, creating parent directories as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [asdict(e) for e in entries.values()]
    path.write_text(json.dumps(payload, indent=2))


def upsert_entry(
    entry: ScheduleEntry, path: Path = DEFAULT_STORE
) -> None:
    """Insert or update a single *entry* in the store."""
    entries = load_store(path)
    entries[entry.job_name] = entry
    save_store(entries, path)


def get_due_jobs(
    entries: dict[str, ScheduleEntry], now_iso: str
) -> list[ScheduleEntry]:
    """Return enabled entries whose next_run is at or before *now_iso*."""
    due = []
    for entry in entries.values():
        if not entry.enabled:
            continue
        if entry.next_run is None or entry.next_run <= now_iso:
            due.append(entry)
    return due
