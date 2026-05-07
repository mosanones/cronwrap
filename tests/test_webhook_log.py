"""Tests for cronwrap.webhook_log and cronwrap.webhook_log_hook."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch
import urllib.error

import pytest

from cronwrap.webhook_log import WebhookLogConfig, _build_payload, ship_record
from cronwrap.webhook_log_hook import maybe_ship, _config_from_env


# ---------------------------------------------------------------------------
# WebhookLogConfig validation
# ---------------------------------------------------------------------------

def test_config_valid():
    cfg = WebhookLogConfig(url="https://example.com/hook", timeout=5)
    assert cfg.url == "https://example.com/hook"
    assert cfg.timeout == 5


def test_config_bad_url():
    with pytest.raises(ValueError, match="Invalid webhook URL"):
        WebhookLogConfig(url="ftp://bad")


def test_config_bad_timeout():
    with pytest.raises(ValueError, match="timeout"):
        WebhookLogConfig(url="https://x.com", timeout=0)


# ---------------------------------------------------------------------------
# _build_payload
# ---------------------------------------------------------------------------

_RECORD = {
    "job_name": "backup",
    "status": "success",
    "exit_code": 0,
    "duration": 1.23,
    "started_at": "2024-01-01T00:00:00",
    "finished_at": "2024-01-01T00:00:01",
    "stdout": "done",
    "stderr": "",
}


def test_build_payload_excludes_output_by_default():
    p = _build_payload(_RECORD, include_output=False)
    assert "stdout" not in p
    assert "stderr" not in p
    assert p["job"] == "backup"


def test_build_payload_includes_output_when_requested():
    p = _build_payload(_RECORD, include_output=True)
    assert p["stdout"] == "done"
    assert p["stderr"] == ""


# ---------------------------------------------------------------------------
# ship_record
# ---------------------------------------------------------------------------

def _mock_response(status: int):
    resp = MagicMock()
    resp.status = status
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return resp


def test_ship_record_success():
    cfg = WebhookLogConfig(url="https://example.com/hook")
    with patch("urllib.request.urlopen", return_value=_mock_response(200)) as mock_open:
        result = ship_record(cfg, _RECORD)
    assert result is True
    mock_open.assert_called_once()


def test_ship_record_non_2xx_returns_false():
    cfg = WebhookLogConfig(url="https://example.com/hook")
    with patch("urllib.request.urlopen", return_value=_mock_response(500)):
        result = ship_record(cfg, _RECORD)
    assert result is False


def test_ship_record_network_error_returns_false():
    cfg = WebhookLogConfig(url="https://example.com/hook")
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("conn refused")):
        result = ship_record(cfg, _RECORD)
    assert result is False


# ---------------------------------------------------------------------------
# maybe_ship / _config_from_env
# ---------------------------------------------------------------------------

def test_maybe_ship_no_config_returns_false():
    assert maybe_ship(_RECORD, config=None) is False


def test_maybe_ship_with_config_ships():
    cfg = WebhookLogConfig(url="https://example.com/hook")
    with patch("cronwrap.webhook_log_hook.ship_record", return_value=True) as mock_ship:
        result = maybe_ship(_RECORD, config=cfg)
    assert result is True
    mock_ship.assert_called_once_with(cfg, _RECORD)


def test_config_from_env_missing(monkeypatch):
    monkeypatch.delenv("CRONWRAP_WEBHOOK_LOG_URL", raising=False)
    assert _config_from_env() is None


def test_config_from_env_present(monkeypatch):
    monkeypatch.setenv("CRONWRAP_WEBHOOK_LOG_URL", "https://env.example.com")
    monkeypatch.setenv("CRONWRAP_WEBHOOK_LOG_TIMEOUT", "15")
    monkeypatch.setenv("CRONWRAP_WEBHOOK_LOG_INCLUDE_OUTPUT", "true")
    cfg = _config_from_env()
    assert cfg is not None
    assert cfg.url == "https://env.example.com"
    assert cfg.timeout == 15
    assert cfg.include_output is True
