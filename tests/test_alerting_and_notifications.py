"""Tests for cronwrap.alerting and cronwrap.notifications."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from cronwrap.alerting import AlertConfig, send_email_alert, send_webhook_alert
from cronwrap.executor import ExecutionResult
from cronwrap.notifications import (
    build_alert_body,
    build_alert_subject,
    dispatch_alert,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def ok_result() -> ExecutionResult:
    return ExecutionResult(returncode=0, stdout="all good", stderr="", duration=1.2, timed_out=False)


@pytest.fixture()
def fail_result() -> ExecutionResult:
    return ExecutionResult(returncode=1, stdout="", stderr="boom", duration=0.5, timed_out=False)


@pytest.fixture()
def timeout_result() -> ExecutionResult:
    return ExecutionResult(returncode=-1, stdout="", stderr="", duration=30.0, timed_out=True)


# ---------------------------------------------------------------------------
# build_alert_subject
# ---------------------------------------------------------------------------

def test_subject_failure(fail_result):
    assert "FAILED" in build_alert_subject("my-job", fail_result)
    assert "my-job" in build_alert_subject("my-job", fail_result)


def test_subject_success(ok_result):
    assert "OK" in build_alert_subject("my-job", ok_result)


# ---------------------------------------------------------------------------
# build_alert_body
# ---------------------------------------------------------------------------

def test_body_contains_stderr(fail_result):
    body = build_alert_body("my-job", fail_result)
    assert "boom" in body
    assert "Exit code: 1" in body


def test_body_timeout_warning(timeout_result):
    body = build_alert_body("my-job", timeout_result)
    assert "timeout" in body.lower()


# ---------------------------------------------------------------------------
# send_email_alert
# ---------------------------------------------------------------------------

def test_email_no_recipients_returns_false():
    cfg = AlertConfig(to_addresses=[])
    assert send_email_alert(cfg, "subj", "body") is False


def test_email_sent_successfully():
    cfg = AlertConfig(to_addresses=["ops@example.com"])
    mock_smtp = MagicMock()
    mock_smtp.__enter__ = lambda s: s
    mock_smtp.__exit__ = MagicMock(return_value=False)
    with patch("smtplib.SMTP", return_value=mock_smtp):
        result = send_email_alert(cfg, "subj", "body")
    assert result is True
    mock_smtp.send_message.assert_called_once()


def test_email_smtp_error_returns_false():
    cfg = AlertConfig(to_addresses=["ops@example.com"])
    with patch("smtplib.SMTP", side_effect=OSError("connection refused")):
        assert send_email_alert(cfg, "subj", "body") is False


# ---------------------------------------------------------------------------
# send_webhook_alert
# ---------------------------------------------------------------------------

def test_webhook_sent_successfully():
    """send_webhook_alert returns True when the HTTP request succeeds."""
    cfg = AlertConfig(to_addresses=[], webhook_url="https://hooks.example.com/notify")
    mock_response = MagicMock()
    mock_response.status_code = 200
    with patch("requests.post", return_value=mock_response) as mock_post:
        result = send_webhook_alert(cfg, "subj", "body")
    assert result is True
    mock_post.assert_called_once()


def test_webhook_no_url_returns_false():
    """send_webhook_alert returns False immediately when no webhook URL is configured."""
    cfg = AlertConfig(to_addresses=[], webhook_url=None)
    assert send_webhook_alert(cfg, "subj", "body") is False


def test_webhook_request_error_returns_false():
    """send_webhook_alert returns False when the HTTP request raises an exception."""
    cfg = AlertConfig(to_addresses=[], webhook_url="https://hooks.example.com/notify")
    with patch("requests.post", side_effect=OSError("network error")):
        assert send_webhook_alert(cfg, "subj", "body") is False
