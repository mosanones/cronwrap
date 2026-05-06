"""CLI helpers for displaying captured command output from run history."""

from __future__ import annotations

from typing import Optional

from cronwrap.history import RunRecord, load_history
from cronwrap.output_capture import CapturedOutput


def _record_to_captured(record: RunRecord) -> Optional[CapturedOutput]:
    """Extract a CapturedOutput from a RunRecord if output fields are present."""
    stdout = getattr(record, "stdout", None) or ""
    stderr = getattr(record, "stderr", None) or ""
    truncated = getattr(record, "truncated", False)
    if not stdout and not stderr:
        return None
    return CapturedOutput(stdout=stdout, stderr=stderr, truncated=truncated)


def render_record_output(record: RunRecord) -> str:
    """Render output section for a single RunRecord."""
    lines: list[str] = []
    lines.append(f"Job   : {record.job_name}")
    lines.append(f"Run   : {record.timestamp}")
    lines.append(f"Status: {record.status}")

    captured = _record_to_captured(record)
    if captured is None:
        lines.append("Output: (none)")
        return "\n".join(lines)

    if captured.truncated:
        lines.append("Output: [truncated]")

    if captured.stdout:
        lines.append("--- stdout ---")
        lines.append(captured.stdout.rstrip())

    if captured.stderr:
        lines.append("--- stderr ---")
        lines.append(captured.stderr.rstrip())

    if not captured.stdout and not captured.stderr:
        lines.append("Output: (empty)")

    return "\n".join(lines)


def render_latest_output(job_name: str, history_path: str) -> str:
    """Render output for the most recent run of *job_name*."""
    records = load_history(history_path)
    job_records = [r for r in records if r.job_name == job_name]
    if not job_records:
        return f"No history found for job '{job_name}'."
    latest = job_records[-1]
    return render_record_output(latest)


def render_all_outputs(job_name: str, history_path: str, limit: int = 10) -> str:
    """Render output for the last *limit* runs of *job_name*."""
    records = load_history(history_path)
    job_records = [r for r in records if r.job_name == job_name][-limit:]
    if not job_records:
        return f"No history found for job '{job_name}'."
    separator = "\n" + "=" * 60 + "\n"
    return separator.join(render_record_output(r) for r in job_records)
