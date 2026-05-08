"""CLI rendering helpers for runbook entries."""
from __future__ import annotations

from typing import List, Optional

from cronwrap.runbook import RunbookEntry, RunbookIndex, load_runbook_index


def render_runbook(entry: RunbookEntry) -> str:
    lines: List[str] = []
    lines.append(f"Job      : {entry.job_name}")
    lines.append(f"URL      : {entry.url or '(none)'}")
    lines.append(f"Notes    : {entry.notes or '(none)'}")
    tag_str = ", ".join(sorted(entry.tags)) if entry.tags else "(none)"
    lines.append(f"Tags     : {tag_str}")
    return "\n".join(lines)


def render_all_runbooks(store_dir: str) -> str:
    index = load_runbook_index(store_dir)
    if not index:
        return "No runbook entries found."
    sections = [render_runbook(e) for e in sorted(index.values(),
                                                   key=lambda e: e.job_name)]
    return ("\n" + "-" * 40 + "\n").join(sections)


def render_runbook_search(store_dir: str, tag: Optional[str] = None,
                          url_only: bool = False) -> str:
    index = load_runbook_index(store_dir)
    results = list(index.values())
    if tag:
        results = [e for e in results if tag in e.tags]
    if url_only:
        results = [e for e in results if e.url]
    if not results:
        return "No matching runbook entries."
    lines: List[str] = []
    for entry in sorted(results, key=lambda e: e.job_name):
        url_part = f" -> {entry.url}" if entry.url else ""
        lines.append(f"  {entry.job_name}{url_part}")
    return "\n".join(lines)
