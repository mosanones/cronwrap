"""Job label management — attach arbitrary key/value labels to jobs."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

LabelIndex = Dict[str, Dict[str, str]]  # job_name -> {key: value}


def load_label_index(path: Path) -> LabelIndex:
    """Load label index from *path*; return empty dict on missing/corrupt file."""
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
        if not isinstance(data, dict):
            return {}
        return {k: dict(v) for k, v in data.items() if isinstance(v, dict)}
    except (json.JSONDecodeError, ValueError):
        return {}


def save_label_index(path: Path, index: LabelIndex) -> None:
    """Persist *index* to *path* as JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(index, indent=2))


def set_labels(index: LabelIndex, job_name: str, labels: Dict[str, str]) -> LabelIndex:
    """Merge *labels* into the label set for *job_name*."""
    existing = dict(index.get(job_name, {}))
    existing.update(labels)
    return {**index, job_name: existing}


def remove_labels(index: LabelIndex, job_name: str, keys: List[str]) -> LabelIndex:
    """Remove *keys* from the label set for *job_name*."""
    existing = dict(index.get(job_name, {}))
    for k in keys:
        existing.pop(k, None)
    updated = dict(index)
    if existing:
        updated[job_name] = existing
    else:
        updated.pop(job_name, None)
    return updated


def get_labels(index: LabelIndex, job_name: str) -> Dict[str, str]:
    """Return labels for *job_name* (empty dict if none)."""
    return dict(index.get(job_name, {}))


def find_jobs_by_label(index: LabelIndex, key: str, value: Optional[str] = None) -> List[str]:
    """Return job names that have *key* (optionally matching *value*)."""
    results = []
    for job, labels in index.items():
        if key in labels:
            if value is None or labels[key] == value:
                results.append(job)
    return sorted(results)
