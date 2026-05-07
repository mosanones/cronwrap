"""Track and report estimated compute cost per job run."""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional


@dataclass
class CostEntry:
    job_name: str
    timestamp: str          # ISO-8601
    duration_seconds: float
    cost_per_second: float  # e.g. 0.000010 USD
    currency: str = "USD"

    @property
    def total_cost(self) -> float:
        return round(self.duration_seconds * self.cost_per_second, 8)


def _cost_path(store_dir: str) -> Path:
    return Path(store_dir) / "cost_log.json"


def load_cost_log(store_dir: str) -> List[CostEntry]:
    path = _cost_path(store_dir)
    if not path.exists():
        return []
    try:
        raw = json.loads(path.read_text())
        return [CostEntry(**r) for r in raw]
    except Exception:
        return []


def save_cost_log(store_dir: str, entries: List[CostEntry]) -> None:
    path = _cost_path(store_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps([asdict(e) for e in entries], indent=2))


def append_cost_entry(store_dir: str, entry: CostEntry) -> None:
    entries = load_cost_log(store_dir)
    entries.append(entry)
    save_cost_log(store_dir, entries)


def job_total_cost(store_dir: str, job_name: str) -> float:
    entries = load_cost_log(store_dir)
    return round(sum(e.total_cost for e in entries if e.job_name == job_name), 8)


def all_job_totals(store_dir: str) -> dict:
    entries = load_cost_log(store_dir)
    totals: dict = {}
    for e in entries:
        totals[e.job_name] = round(totals.get(e.job_name, 0.0) + e.total_cost, 8)
    return totals
