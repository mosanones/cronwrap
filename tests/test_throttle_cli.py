"""Tests for cronwrap.throttle_cli render helpers."""
from __future__ import annotations

import datetime
import json
import pathlib

import pytest

from cronwrap.throttle_cli import render_throttle_status, _fmt_window


def _iso(seconds_ago: float = 0) -> str:
    ts = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
        seconds=seconds_ago
    )
    return ts.isoformat()


def _record(job_name: str, seconds_ago: float = 0) -> dict:
    return {
        "job_name": job_name,
        "started_at": _iso(seconds_ago),
        "finished_at": _iso(seconds_ago),
        "exit_code": 0,
        "stdout": "",
        "stderr": "",
        "duration": 0.1,
        "timed_out": False,
    }


@pytest.fixture()
def history_path(tmp_path: pathlib.Path) -> str:
    return str(tmp_path / "history.json")


# ---------------------------------------------------------------------------
# _fmt_window
# ---------------------------------------------------------------------------

def test_fmt_window_seconds() -> None:
    assert _fmt_window(45) == "45s"


def test_fmt_window_minutes() -> None:
    assert _fmt_window(300) == "5m"


def test_fmt_window_hours() -> None:
    assert _fmt_window(7200) == "2h"


# ---------------------------------------------------------------------------
# render_throttle_status
# ---------------------------------------------------------------------------

def test_render_no_history(history_path: str) -> None:
    out = render_throttle_status(history_path)
    assert "No job history" in out


def test_render_shows_job_name(history_path: str) -> None:
    data = [_record("backup-job", 30)]
    pathlib.Path(history_path).write_text(json.dumps(data))
    out = render_throttle_status(history_path, window_seconds=60, max_runs=5)
    assert "backup-job" in out


def test_render_ok_status(history_path: str) -> None:
    data = [_record("myjob", 10)]
    pathlib.Path(history_path).write_text(json.dumps(data))
    out = render_throttle_status(history_path, window_seconds=60, max_runs=5)
    assert "OK" in out


def test_render_throttled_status(history_path: str) -> None:
    data = [_record("myjob", i * 5) for i in range(5)]
    pathlib.Path(history_path).write_text(json.dumps(data))
    out = render_throttle_status(history_path, window_seconds=120, max_runs=5)
    assert "THROTTLED" in out


def test_render_multiple_jobs_sorted(history_path: str) -> None:
    data = [_record("zebra", 10), _record("alpha", 20)]
    pathlib.Path(history_path).write_text(json.dumps(data))
    out = render_throttle_status(history_path, window_seconds=60, max_runs=5)
    alpha_pos = out.index("alpha")
    zebra_pos = out.index("zebra")
    assert alpha_pos < zebra_pos


def test_render_includes_window_and_limit(history_path: str) -> None:
    data = [_record("job", 5)]
    pathlib.Path(history_path).write_text(json.dumps(data))
    out = render_throttle_status(history_path, window_seconds=3600, max_runs=10)
    assert "1h" in out
    assert "10" in out
