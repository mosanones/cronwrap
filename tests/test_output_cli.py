"""Tests for cronwrap.output_cli."""

from __future__ import annotations

import json
import pathlib
import pytest

from cronwrap.output_cli import (
    render_record_output,
    render_latest_output,
    render_all_outputs,
    _record_to_captured,
)
from cronwrap.history import RunRecord


def _make_record(
    job_name: str = "myjob",
    status: str = "success",
    stdout: str = "",
    stderr: str = "",
    truncated: bool = False,
    timestamp: str = "2024-01-01T00:00:00",
) -> RunRecord:
    return RunRecord(
        job_name=job_name,
        timestamp=timestamp,
        status=status,
        exit_code=0 if status == "success" else 1,
        duration=1.0,
        stdout=stdout,
        stderr=stderr,
        truncated=truncated,
    )


@pytest.fixture()
def history_path(tmp_path: pathlib.Path) -> str:
    return str(tmp_path / "history.json")


def _write_history(path: str, records: list[RunRecord]) -> None:
    data = [r.__dict__ for r in records]
    pathlib.Path(path).write_text(json.dumps(data))


# --- _record_to_captured ---

def test_record_to_captured_no_output_returns_none():
    r = _make_record()
    assert _record_to_captured(r) is None


def test_record_to_captured_with_stdout():
    r = _make_record(stdout="hello")
    captured = _record_to_captured(r)
    assert captured is not None
    assert captured.stdout == "hello"


def test_record_to_captured_truncated_flag():
    r = _make_record(stdout="x" * 10, truncated=True)
    captured = _record_to_captured(r)
    assert captured is not None
    assert captured.truncated is True


# --- render_record_output ---

def test_render_record_output_no_output():
    r = _make_record()
    result = render_record_output(r)
    assert "(none)" in result
    assert "myjob" in result


def test_render_record_output_with_stdout():
    r = _make_record(stdout="hello world")
    result = render_record_output(r)
    assert "stdout" in result
    assert "hello world" in result


def test_render_record_output_with_stderr():
    r = _make_record(stderr="oops")
    result = render_record_output(r)
    assert "stderr" in result
    assert "oops" in result


def test_render_record_output_truncated_label():
    r = _make_record(stdout="data", truncated=True)
    result = render_record_output(r)
    assert "truncated" in result


# --- render_latest_output ---

def test_render_latest_output_no_history(history_path):
    result = render_latest_output("myjob", history_path)
    assert "No history" in result


def test_render_latest_output_returns_last_record(history_path):
    records = [
        _make_record(stdout="first", timestamp="2024-01-01T00:00:00"),
        _make_record(stdout="second", timestamp="2024-01-02T00:00:00"),
    ]
    _write_history(history_path, records)
    result = render_latest_output("myjob", history_path)
    assert "second" in result
    assert "first" not in result


# --- render_all_outputs ---

def test_render_all_outputs_no_history(history_path):
    result = render_all_outputs("myjob", history_path)
    assert "No history" in result


def test_render_all_outputs_multiple_records(history_path):
    records = [
        _make_record(stdout="run1", timestamp="2024-01-01T00:00:00"),
        _make_record(stdout="run2", timestamp="2024-01-02T00:00:00"),
    ]
    _write_history(history_path, records)
    result = render_all_outputs("myjob", history_path)
    assert "run1" in result
    assert "run2" in result


def test_render_all_outputs_respects_limit(history_path):
    records = [_make_record(stdout=f"run{i}", timestamp=f"2024-01-0{i+1}T00:00:00") for i in range(5)]
    _write_history(history_path, records)
    result = render_all_outputs("myjob", history_path, limit=2)
    assert "run3" in result
    assert "run4" in result
    assert "run0" not in result
