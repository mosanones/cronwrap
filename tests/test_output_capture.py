"""Tests for cronwrap.output_capture and cronwrap.output_hook."""
from __future__ import annotations

import pytest

from cronwrap.output_capture import (
    CapturedOutput,
    DEFAULT_MAX_BYTES,
    TRUNCATION_NOTICE,
    capture,
    render_output,
    _truncate_to_bytes,
)
from cronwrap.output_hook import attach_to_record, extract_output, summarise


# ---------------------------------------------------------------------------
# _truncate_to_bytes
# ---------------------------------------------------------------------------

def test_truncate_to_bytes_short_string_unchanged():
    assert _truncate_to_bytes("hello", 100) == "hello"


def test_truncate_to_bytes_exact_length_unchanged():
    text = "a" * 10
    assert _truncate_to_bytes(text, 10) == text


def test_truncate_to_bytes_long_string_truncated():
    text = "x" * 200
    result = _truncate_to_bytes(text, 50)
    assert len(result.encode()) <= 50


# ---------------------------------------------------------------------------
# capture()
# ---------------------------------------------------------------------------

def test_capture_no_truncation_when_small():
    co = capture("hello", "world")
    assert co.stdout == "hello"
    assert co.stderr == "world"
    assert not co.stdout_truncated
    assert not co.stderr_truncated


def test_capture_truncates_large_stdout():
    big = "A" * (DEFAULT_MAX_BYTES + 100)
    co = capture(big, "")
    assert co.stdout_truncated
    assert TRUNCATION_NOTICE in co.stdout
    assert not co.stderr_truncated


def test_capture_truncates_large_stderr():
    big = "E" * (DEFAULT_MAX_BYTES + 100)
    co = capture("", big)
    assert co.stderr_truncated
    assert TRUNCATION_NOTICE in co.stderr


def test_capture_invalid_max_bytes_raises():
    with pytest.raises(ValueError):
        capture("x", "y", max_bytes=0)


# ---------------------------------------------------------------------------
# CapturedOutput properties
# ---------------------------------------------------------------------------

def test_has_output_false_when_empty():
    co = CapturedOutput()
    assert not co.has_output


def test_has_output_true_with_stdout():
    co = CapturedOutput(stdout="hi")
    assert co.has_output


def test_combined_includes_both_streams():
    co = CapturedOutput(stdout="out line", stderr="err line")
    combined = co.combined
    assert "out line" in combined
    assert "err line" in combined


def test_combined_empty_when_no_output():
    co = CapturedOutput()
    assert co.combined == ""


def test_post_init_invalid_max_bytes_raises():
    with pytest.raises(ValueError):
        CapturedOutput(max_bytes=0)


# ---------------------------------------------------------------------------
# render_output()
# ---------------------------------------------------------------------------

def test_render_output_no_output():
    co = CapturedOutput()
    assert render_output(co) == "(no output)"


def test_render_output_contains_stdout_label():
    co = CapturedOutput(stdout="hello")
    rendered = render_output(co)
    assert "STDOUT" in rendered
    assert "hello" in rendered


def test_render_output_shows_truncated_marker():
    co = CapturedOutput(stdout="x", stdout_truncated=True)
    rendered = render_output(co)
    assert "truncated" in rendered


# ---------------------------------------------------------------------------
# output_hook helpers
# ---------------------------------------------------------------------------

class _FakeResult:
    def __init__(self, stdout="", stderr=""):
        self.stdout = stdout
        self.stderr = stderr


def test_extract_output_returns_captured_output():
    result = _FakeResult(stdout="ok", stderr="warn")
    co = extract_output(result)  # type: ignore[arg-type]
    assert co.stdout == "ok"
    assert co.stderr == "warn"


def test_attach_to_record_adds_fields():
    co = CapturedOutput(stdout="out", stderr="err", stdout_truncated=False, stderr_truncated=True)
    record = {"job": "test"}
    attach_to_record(record, co)
    assert record["stdout"] == "out"
    assert record["stderr"] == "err"
    assert record["stderr_truncated"] is True


def test_summarise_short_output_unchanged():
    co = CapturedOutput(stdout="line1\nline2")
    result = summarise(co, max_lines=10)
    assert "line1" in result


def test_summarise_long_output_trimmed():
    lines = [f"line{i}" for i in range(50)]
    co = CapturedOutput(stdout="\n".join(lines))
    result = summarise(co, max_lines=5)
    assert "omitted" in result
    assert "line49" in result


def test_summarise_empty_returns_no_output():
    co = CapturedOutput()
    assert summarise(co) == "(no output)"
