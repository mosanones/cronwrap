"""Integration hook: attach/read labels during job execution."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from cronwrap.label import (
    get_labels,
    load_label_index,
    save_label_index,
    set_labels,
)

_DEFAULT_PATH = Path(".cronwrap") / "labels.json"


def get_job_labels(job_name: str, store: Path = _DEFAULT_PATH) -> Dict[str, str]:
    """Return labels currently attached to *job_name*."""
    index = load_label_index(store)
    return get_labels(index, job_name)


def apply_job_labels(
    job_name: str,
    labels: Dict[str, str],
    store: Path = _DEFAULT_PATH,
) -> None:
    """Merge *labels* onto *job_name* and persist to *store*."""
    index = load_label_index(store)
    index = set_labels(index, job_name, labels)
    save_label_index(store, index)


def label_matches(
    job_name: str,
    key: str,
    value: Optional[str] = None,
    store: Path = _DEFAULT_PATH,
) -> bool:
    """Return True if *job_name* has *key* (optionally equal to *value*)."""
    labels = get_job_labels(job_name, store)
    if key not in labels:
        return False
    return value is None or labels[key] == value
