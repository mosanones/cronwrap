"""Tests for cronwrap.throttle and cronwrap.throttle_hook."""
from __future__ import annotations

import datetime
import json
import pathlib

import pytest

from cronwrap.throttle import (
    ThrottleConfig,
    ThrottleExceeded,
    _recent_runs,
    check_throttle,
)
from cronwrap.throttle_hook import maybe_throttle


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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
        "duration": 0.0,
        "timed_out": False,
    }


@pytest.fixture()
def history_path(tmp_path: pathlib.Path) -> str:
    return str(tmp_path / "history.json")


# ---------------------------------------------------------------------------
# ThrottleConfig validation
# ---------------------------------------------------------------------------

def test_throttle_config_valid() -> None:
    cfg = ThrottleConfig(max_runs=3, window_seconds=60)
    assert cfg.max_runs == 3
    assert cfg.window_seconds == 60


def test_throttle_config_bad_max_runs() -> None:
    with pytest.raises(ValueError, match="max_runs"):
        ThrottleConfig(max_runs=0, window_seconds=60)


def test_throttle_config_bad_window() -> None:
    with pytest.raises(ValueError, match="window_seconds"):
        ThrottleConfig(max_runs=1, window_seconds=0)


# ---------------------------------------------------------------------------
# _recent_runs
# ---------------------------------------------------------------------------

def test_recent_runs_counts_only_window(tmp_path: pathlib.Path) -> None:
    from cronwrap.history import RunRecord

    records = [
        RunRecord(**_record("job", seconds_ago=10)),
        RunRecord(**_record("job", seconds_ago=50)),
        RunRecord(**_record("job", seconds_ago=200)),  # outside 120 s window
        RunRecord(**_record("other", seconds_ago=5)),  # different job
    ]
    assert _recent_runs(records, "job", 120) == 2


def test_recent_runs_empty_history() -> None:
    assert _recent_runs([], "job", 60) == 0


# ---------------------------------------------------------------------------
# check_throttle
# ---------------------------------------------------------------------------

def test_check_throttle_passes_when_under_limit(
    history_path: str, tmp_path: pathlib.Path
) -> None:
    records = [_record("myjob", seconds_ago=5)]
    pathlib.Path(history_path).write_text(json.dumps(records))
    cfg = ThrottleConfig(max_runs=3, window_seconds=60)
    check_throttle("myjob", cfg, history_path)  # should not raise


def test_check_throttle_raises_when_limit_reached(
    history_path: str, tmp_path: pathlib.Path
) -> None:
    records = [
        _record("myjob", seconds_ago=5),
        _record("myjob", seconds_ago=15),
        _record("myjob", seconds_ago=25),
    ]
    pathlib.Path(history_path).write_text(json.dumps(records))
    cfg = ThrottleConfig(max_runs=3, window_seconds=60)
    with pytest.raises(ThrottleExceeded) as exc_info:
        check_throttle("myjob", cfg, history_path)
    assert "myjob" in str(exc_info.value)
    assert exc_info.value.runs == 3


def test_check_throttle_missing_history_file(history_path: str) -> None:
    """No history file → 0 runs → should not raise."""
    cfg = ThrottleConfig(max_runs=1, window_seconds=60)
    check_throttle("myjob", cfg, history_path)  # should not raise


# ---------------------------------------------------------------------------
# maybe_throttle hook
# ---------------------------------------------------------------------------

def test_maybe_throttle_skips_when_params_none(history_path: str) -> None:
    maybe_throttle("job", history_path, max_runs=None, window_seconds=None)


def test_maybe_throttle_skips_partial_params(history_path: str) -> None:
    maybe_throttle("job", history_path, max_runs=2, window_seconds=None)
    maybe_throttle("job", history_path, max_runs=None, window_seconds=30)


def test_maybe_throttle_raises_when_exceeded(
    history_path: str, tmp_path: pathlib.Path
) -> None:
    records = [_record("job", 5), _record("job", 10)]
    pathlib.Path(history_path).write_text(json.dumps(records))
    with pytest.raises(ThrottleExceeded):
        maybe_throttle("job", history_path, max_runs=2, window_seconds=60)
