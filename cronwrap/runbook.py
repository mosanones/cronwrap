"""Runbook links: attach documentation URLs and notes to jobs."""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class RunbookEntry:
    job_name: str
    url: Optional[str] = None
    notes: str = ""
    tags: List[str] = field(default_factory=list)


RunbookIndex = Dict[str, RunbookEntry]


def _runbook_path(store_dir: str) -> Path:
    return Path(store_dir) / "runbooks.json"


def load_runbook_index(store_dir: str) -> RunbookIndex:
    path = _runbook_path(store_dir)
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text())
        return {
            k: RunbookEntry(**v) for k, v in raw.items()
        }
    except Exception:
        return {}


def save_runbook_index(store_dir: str, index: RunbookIndex) -> None:
    path = _runbook_path(store_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({k: asdict(v) for k, v in index.items()}, indent=2))


def set_runbook(store_dir: str, job_name: str, url: Optional[str] = None,
               notes: str = "", tags: Optional[List[str]] = None) -> RunbookEntry:
    index = load_runbook_index(store_dir)
    entry = RunbookEntry(job_name=job_name, url=url, notes=notes,
                         tags=tags or [])
    index[job_name] = entry
    save_runbook_index(store_dir, index)
    return entry


def get_runbook(store_dir: str, job_name: str) -> Optional[RunbookEntry]:
    return load_runbook_index(store_dir).get(job_name)


def remove_runbook(store_dir: str, job_name: str) -> bool:
    index = load_runbook_index(store_dir)
    if job_name not in index:
        return False
    del index[job_name]
    save_runbook_index(store_dir, index)
    return True
