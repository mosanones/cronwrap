"""CLI helpers for displaying captured output from history records."""
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from cronwrap.output_capture import CapturedOutput, render_output


def _record_to_captured(record: dict) -> CapturedOutput:
    """Reconstruct a CapturedOutput from a stored history record dict."""
    return CapturedOutput(
        stdout=record.get("stdout", ""),
        stderr=record.get("stderr", ""),
        stdout_truncated=record.get("stdout_truncated", False),
        stderr_truncated=record.get("stderr_truncated", False),
    )


def render_record_output(record: dict, width: int = 80) -> str:
    """Return a formatted output block for a single history record."""
    captured = _record_to_captured(record)
    job = record.get("job_name", "unknown")
    ts = record.get("started_at", "?")
    header = f"Job: {job}  |  Started: {ts}"
    body = render_output(captured, width=width)
    return f"{header}\n{body}"


def render_latest_output(history_path: Path, job_name: str, width: int = 80) -> str:
    """Load history and render output for the most recent run of *job_name*."""
    if not history_path.exists():
        return f"No history file found at {history_path}"
    try:
        records: List[dict] = json.loads(history_path.read_text())
    except (json.JSONDecodeError, OSError):
        return "History file is corrupt or unreadable."

    matches = [r for r in records if r.get("job_name") == job_name]
    if not matches:
        return f"No runs recorded for job '{job_name}'."

    latest = matches[-1]
    return render_record_output(latest, width=width)


def render_all_outputs(history_path: Path, job_name: str, width: int = 80) -> str:
    """Render captured output for every recorded run of *job_name*."""
    if not history_path.exists():
        return f"No history file found at {history_path}"
    try:
        records: List[dict] = json.loads(history_path.read_text())
    except (json.JSONDecodeError, OSError):
        return "History file is corrupt or unreadable."

    matches = [r for r in records if r.get("job_name") == job_name]
    if not matches:
        return f"No runs recorded for job '{job_name}'."

    separator = "=" * min(width, 80)
    blocks = [render_record_output(r, width=width) for r in matches]
    return ("\n" + separator + "\n").join(blocks)
