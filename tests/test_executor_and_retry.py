"""Tests for cronwrap executor and retry modules."""

import pytest
from unittest.mock import patch, MagicMock
import subprocess

from cronwrap.executor import run_command, ExecutionResult
from cronwrap.retry import run_with_retry
from cronwrap.config import JobConfig
from cronwrap.runner import run_job


# ---------------------------------------------------------------------------
# executor tests
# ---------------------------------------------------------------------------

def test_run_command_success():
    result = run_command("echo hello")
    assert result.success
    assert result.exit_code == 0
    assert "hello" in result.stdout
    assert result.attempt == 1


def test_run_command_failure():
    result = run_command("exit 1", attempt=1)
    assert not result.success
    assert result.exit_code == 1


def test_run_command_timeout():
    result = run_command("sleep 10", timeout=1)
    assert not result.success
    assert result.exit_code == -1
    assert "timed out" in result.stderr


# ---------------------------------------------------------------------------
# retry tests
# ---------------------------------------------------------------------------

def test_retry_succeeds_on_first_attempt():
    result = run_with_retry("echo ok", retries=3, delay=0)
    assert result.success
    assert result.attempt == 1


def test_retry_exhausts_all_attempts():
    result = run_with_retry("exit 2", retries=3, delay=0)
    assert not result.success
    assert result.attempt == 3


def test_retry_callback_called_on_failure():
    calls = []
    run_with_retry("exit 1", retries=2, delay=0, on_retry=lambda r: calls.append(r))
    assert len(calls) == 1  # called after first failure, not after last


def test_retry_invalid_retries():
    with pytest.raises(ValueError, match="retries must be >= 1"):
        run_with_retry("echo x", retries=0)


# ---------------------------------------------------------------------------
# config validation tests
# ---------------------------------------------------------------------------

def test_config_validates_ok():
    cfg = JobConfig(command="echo hi", retries=2, timeout=30)
    cfg.validate()  # should not raise


def test_config_empty_command_raises():
    with pytest.raises(ValueError, match="command"):
        JobConfig(command="").validate()


def test_config_bad_log_level_raises():
    with pytest.raises(ValueError, match="log_level"):
        JobConfig(command="echo x", log_level="VERBOSE").validate()


# ---------------------------------------------------------------------------
# runner integration test
# ---------------------------------------------------------------------------

def test_run_job_success():
    cfg = JobConfig(command="echo integration", name="test-job")
    result = run_job(cfg)
    assert result.success


def test_run_job_failure_no_alert():
    cfg = JobConfig(command="exit 42", name="fail-job", retries=1, alert_on_failure=False)
    result = run_job(cfg)
    assert not result.success
    assert result.exit_code == 42
