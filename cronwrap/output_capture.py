"""Capture and truncate stdout/stderr from job runs for storage and display."""
from __future__ import annotations

import textwrap
from dataclasses import dataclass, field
from typing import Optional

DEFAULT_MAX_BYTES = 8192  # 8 KB per stream
TRUNCATION_NOTICE = "\n... [output truncated] ..."


@dataclass
class CapturedOutput:
    stdout: str = ""
    stderr: str = ""
    stdout_truncated: bool = False
    stderr_truncated: bool = False
    max_bytes: int = field(default=DEFAULT_MAX_BYTES, repr=False)

    def __post_init__(self) -> None:
        if self.max_bytes < 1:
            raise ValueError("max_bytes must be >= 1")

    @property
    def has_output(self) -> bool:
        return bool(self.stdout or self.stderr)

    @property
    def combined(self) -> str:
        parts = []
        if self.stdout:
            parts.append(f"[stdout]\n{self.stdout}")
        if self.stderr:
            parts.append(f"[stderr]\n{self.stderr}")
        return "\n".join(parts)


def capture(stdout_raw: str, stderr_raw: str, max_bytes: int = DEFAULT_MAX_BYTES) -> CapturedOutput:
    """Truncate raw output strings and return a CapturedOutput instance."""
    if max_bytes < 1:
        raise ValueError("max_bytes must be >= 1")

    stdout_trunc = False
    stderr_trunc = False

    if len(stdout_raw.encode()) > max_bytes:
        stdout_raw = _truncate_to_bytes(stdout_raw, max_bytes) + TRUNCATION_NOTICE
        stdout_trunc = True

    if len(stderr_raw.encode()) > max_bytes:
        stderr_raw = _truncate_to_bytes(stderr_raw, max_bytes) + TRUNCATION_NOTICE
        stderr_trunc = True

    return CapturedOutput(
        stdout=stdout_raw,
        stderr=stderr_raw,
        stdout_truncated=stdout_trunc,
        stderr_truncated=stderr_trunc,
        max_bytes=max_bytes,
    )


def _truncate_to_bytes(text: str, max_bytes: int) -> str:
    """Truncate *text* so its UTF-8 encoding fits within *max_bytes*."""
    encoded = text.encode()
    if len(encoded) <= max_bytes:
        return text
    return encoded[:max_bytes].decode(errors="ignore")


def render_output(captured: CapturedOutput, width: int = 80) -> str:
    """Return a human-readable block suitable for logs or alert bodies."""
    if not captured.has_output:
        return "(no output)"
    lines = []
    border = "-" * min(width, 80)
    for label, text, trunc in [
        ("STDOUT", captured.stdout, captured.stdout_truncated),
        ("STDERR", captured.stderr, captured.stderr_truncated),
    ]:
        if not text:
            continue
        lines.append(f"{border}")
        lines.append(f"  {label}{'  [truncated]' if trunc else ''}")
        lines.append(border)
        lines.append(textwrap.indent(text.rstrip(), "  "))
    lines.append(border)
    return "\n".join(lines)
