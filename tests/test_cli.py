"""Tests for the cronwrap CLI."""
from __future__ import annotations

import json
import dataclasses
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from cronwrap.cli import _build_parser, main
from cronwrap.history import RunRecord


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fake_record(job_name="test-job", exit_code=0, timed_out=False, duration=1.23):
    return RunRecord(
        job_name=job_name,
        command="echo hi",
        started_at="2024-01-01T00:00:00",
        finished_at="2024-01-01T00:00:01",
        exit_code=exit_code,
        timed_out=timed_out,
        duration_seconds=duration,
        stdout="",
        stderr="",
        attempts=1,
    )


# ---------------------------------------------------------------------------
# Parser tests
# ---------------------------------------------------------------------------

class TestParser:
    def test_run_defaults(self):
        parser = _build_parser()
        args = parser.parse_args(["run", "echo hello"])
        assert args.cmd == "echo hello"
        assert args.job_name == "unnamed"
        assert args.retries == 0
        assert args.log_level == "INFO"
        assert args.alert_on == ["failure"]

    def test_run_custom_flags(self):
        parser = _build_parser()
        args = parser.parse_args([
            "run", "ls -la",
            "--job-name", "my-job",
            "--timeout", "30",
            "--retries", "3",
            "--log-level", "DEBUG",
            "--alert-on", "failure", "timeout",
        ])
        assert args.job_name == "my-job"
        assert args.timeout == 30.0
        assert args.retries == 3
        assert args.log_level == "DEBUG"
        assert set(args.alert_on) == {"failure", "timeout"}

    def test_history_defaults(self):
        parser = _build_parser()
        args = parser.parse_args(["history"])
        assert args.last == 10
        assert args.job_name is None
        assert not args.as_json

    def test_missing_subcommand_raises(self):
        parser = _build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([])


# ---------------------------------------------------------------------------
# run subcommand
# ---------------------------------------------------------------------------

class TestCmdRun:
    def test_run_success_exits_zero(self, tmp_path):
        hist = tmp_path / "h.json"
        record = _fake_record(exit_code=0)
        with patch("cronwrap.cli.run_job", return_value=record) as mock_run:
            with pytest.raises(SystemExit) as exc:
                main(["run", "echo hi", "--history-file", str(hist)])
        assert exc.value.code == 0
        mock_run.assert_called_once()

    def test_run_failure_exits_nonzero(self, tmp_path):
        hist = tmp_path / "h.json"
        record = _fake_record(exit_code=1)
        with patch("cronwrap.cli.run_job", return_value=record):
            with pytest.raises(SystemExit) as exc:
                main(["run", "false", "--history-file", str(hist)])
        assert exc.value.code == 1


# ---------------------------------------------------------------------------
# history subcommand
# ---------------------------------------------------------------------------

class TestCmdHistory:
    def test_history_plain_output(self, tmp_path, capsys):
        records = [_fake_record("job-a"), _fake_record("job-b", exit_code=1)]
        with patch("cronwrap.cli.load_history", return_value=records):
            with pytest.raises(SystemExit) as exc:
                main(["history", "--history-file", str(tmp_path / "h.json")])
        assert exc.value.code == 0
        out = capsys.readouterr().out
        assert "job-a" in out
        assert "job-b" in out
        assert "FAIL" in out

    def test_history_json_output(self, tmp_path, capsys):
        records = [_fake_record("job-x")]
        with patch("cronwrap.cli.load_history", return_value=records):
            with pytest.raises(SystemExit):
                main(["history", "--json", "--history-file", str(tmp_path / "h.json")])
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data[0]["job_name"] == "job-x"

    def test_history_filter_by_job_name(self, tmp_path, capsys):
        records = [_fake_record("alpha"), _fake_record("beta")]
        with patch("cronwrap.cli.load_history", return_value=records):
            with pytest.raises(SystemExit):
                main(["history", "--job-name", "alpha",
                      "--history-file", str(tmp_path / "h.json")])
        out = capsys.readouterr().out
        assert "alpha" in out
        assert "beta" not in out

    def test_history_empty(self, tmp_path, capsys):
        with patch("cronwrap.cli.load_history", return_value=[]):
            with pytest.raises(SystemExit):
                main(["history", "--history-file", str(tmp_path / "h.json")])
        out = capsys.readouterr().out
        assert "No records found" in out
