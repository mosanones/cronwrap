"""Heartbeat tracking — record periodic pings and detect missed beats."""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

from cronwrap.history import now_iso


@dataclass
class HeartbeatRecord:
    job_name: str
    last_ping: str          # ISO-8601 timestamp
    interval_seconds: int   # expected interval between pings
    missed: bool = False


def _heartbeat_path(store_dir: str) -> Path:
    return Path(store_dir) / "heartbeats.json"


def load_heartbeats(store_dir: str) -> dict[str, HeartbeatRecord]:
    path = _heartbeat_path(store_dir)
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text())
        return {
            k: HeartbeatRecord(**v)
            for k, v in raw.items()
        }
    except Exception:
        return {}


def save_heartbeats(store_dir: str, records: dict[str, HeartbeatRecord]) -> None:
    path = _heartbeat_path(store_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({k: asdict(v) for k, v in records.items()}, indent=2))


def ping(store_dir: str, job_name: str, interval_seconds: int) -> HeartbeatRecord:
    """Record a heartbeat ping for *job_name*."""
    records = load_heartbeats(store_dir)
    record = HeartbeatRecord(
        job_name=job_name,
        last_ping=now_iso(),
        interval_seconds=interval_seconds,
        missed=False,
    )
    records[job_name] = record
    save_heartbeats(store_dir, records)
    return record


def check_missed(store_dir: str) -> list[HeartbeatRecord]:
    """Return records whose last ping is older than their expected interval."""
    import datetime

    records = load_heartbeats(store_dir)
    now = datetime.datetime.now(datetime.timezone.utc)
    missed: list[HeartbeatRecord] = []
    for record in records.values():
        last = datetime.datetime.fromisoformat(record.last_ping)
        if last.tzinfo is None:
            last = last.replace(tzinfo=datetime.timezone.utc)
        age = (now - last).total_seconds()
        if age > record.interval_seconds:
            record.missed = True
            missed.append(record)
    if missed:
        save_heartbeats(store_dir, records)
    return missed
