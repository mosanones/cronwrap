"""Tag-based filtering and grouping for cron jobs."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class TagIndex:
    """Maps tag names to lists of job names."""
    index: Dict[str, List[str]] = field(default_factory=dict)


def load_tag_index(path: Path) -> TagIndex:
    """Load tag index from a JSON file; return empty index on missing/corrupt file."""
    try:
        data = json.loads(path.read_text())
        return TagIndex(index={k: list(v) for k, v in data.items()})
    except (FileNotFoundError, json.JSONDecodeError, TypeError, AttributeError):
        return TagIndex()


def save_tag_index(path: Path, tag_index: TagIndex) -> None:
    """Persist tag index to a JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(tag_index.index, indent=2))


def add_job_tags(tag_index: TagIndex, job_name: str, tags: List[str]) -> TagIndex:
    """Associate a job with one or more tags, deduplicating entries."""
    new_index = {k: list(v) for k, v in tag_index.index.items()}
    for tag in tags:
        jobs = new_index.setdefault(tag, [])
        if job_name not in jobs:
            jobs.append(job_name)
    return TagIndex(index=new_index)


def remove_job_tags(
    tag_index: TagIndex, job_name: str, tags: Optional[List[str]] = None
) -> TagIndex:
    """Remove a job from specific tags, or from all tags if *tags* is None."""
    new_index: Dict[str, List[str]] = {}
    for tag, jobs in tag_index.index.items():
        if tags is None or tag in tags:
            updated = [j for j in jobs if j != job_name]
        else:
            updated = list(jobs)
        if updated:
            new_index[tag] = updated
    return TagIndex(index=new_index)


def jobs_for_tag(tag_index: TagIndex, tag: str) -> List[str]:
    """Return all job names associated with a given tag."""
    return list(tag_index.index.get(tag, []))


def tags_for_job(tag_index: TagIndex, job_name: str) -> List[str]:
    """Return all tags associated with a given job name."""
    return [tag for tag, jobs in tag_index.index.items() if job_name in jobs]
