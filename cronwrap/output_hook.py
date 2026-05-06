"""Hook that attaches captured output to RunRecord and audit events."""
from __future__ import annotations

from typing import Optional

from cronwrap.executor import ExecutionResult
from cronwrap.output_capture import CapturedOutput, capture, DEFAULT_MAX_BYTES


def extract_output(
    result: ExecutionResult,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> CapturedOutput:
    """Build a CapturedOutput from an ExecutionResult's raw streams."""
    stdout_raw = result.stdout or ""
    stderr_raw = result.stderr or ""
    return capture(stdout_raw, stderr_raw, max_bytes=max_bytes)


def attach_to_record(record: dict, captured: CapturedOutput) -> dict:
    """Merge captured output fields into a plain-dict run record.

    Works with the dict representation used by history.RunRecord serialisation.
    Returns the same dict (mutated in-place) for convenience.
    """
    record["stdout"] = captured.stdout
    record["stderr"] = captured.stderr
    record["stdout_truncated"] = captured.stdout_truncated
    record["stderr_truncated"] = captured.stderr_truncated
    return record


def summarise(captured: CapturedOutput, max_lines: int = 10) -> str:
    """Return a short summary (last *max_lines* lines of combined output)."""
    combined = captured.combined
    if not combined:
        return "(no output)"
    lines = combined.splitlines()
    if len(lines) <= max_lines:
        return combined
    kept = lines[-max_lines:]
    omitted = len(lines) - max_lines
    return f"... ({omitted} lines omitted) ...\n" + "\n".join(kept)
