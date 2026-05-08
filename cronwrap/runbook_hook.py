"""Hook that attaches runbook info to a run record's extra metadata."""
from __future__ import annotations

import os
from typing import Any, Dict, Optional

from cronwrap.runbook import get_runbook, RunbookEntry


def _store_dir() -> str:
    return os.environ.get("CRONWRAP_STORE_DIR", ".cronwrap")


def get_runbook_for_job(job_name: str,
                        store_dir: Optional[str] = None) -> Optional[RunbookEntry]:
    return get_runbook(store_dir or _store_dir(), job_name)


def attach_runbook_to_record(record: Dict[str, Any], job_name: str,
                             store_dir: Optional[str] = None) -> None:
    """Mutate *record* in-place, adding runbook metadata when available."""
    entry = get_runbook_for_job(job_name, store_dir)
    if entry is None:
        return
    record.setdefault("runbook", {})
    record["runbook"]["url"] = entry.url
    record["runbook"]["notes"] = entry.notes
    record["runbook"]["tags"] = entry.tags


def runbook_summary(job_name: str, store_dir: Optional[str] = None) -> str:
    """Return a one-line summary suitable for log output."""
    entry = get_runbook_for_job(job_name, store_dir)
    if entry is None:
        return ""
    parts = []
    if entry.url:
        parts.append(f"runbook={entry.url}")
    if entry.notes:
        short = entry.notes[:60] + ("..." if len(entry.notes) > 60 else "")
        parts.append(f"notes='{short}'")
    return " ".join(parts)
