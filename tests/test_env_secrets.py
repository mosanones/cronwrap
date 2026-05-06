"""Tests for cronwrap.env_secrets."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from cronwrap.env_secrets import inject_dotenv, load_dotenv, resolve_secrets


# ---------------------------------------------------------------------------
# load_dotenv
# ---------------------------------------------------------------------------

def test_load_dotenv_missing_file(tmp_path: Path):
    result = load_dotenv(tmp_path / "nonexistent.env")
    assert result == {}


def test_load_dotenv_basic(tmp_path: Path):
    env_file = tmp_path / ".env"
    env_file.write_text("FOO=bar\nBAZ=qux\n")
    result = load_dotenv(env_file)
    assert result == {"FOO": "bar", "BAZ": "qux"}


def test_load_dotenv_strips_quotes(tmp_path: Path):
    env_file = tmp_path / ".env"
    env_file.write_text('KEY="hello world"\nOTHER=\'single\'\n')
    result = load_dotenv(env_file)
    assert result["KEY"] == "hello world"
    assert result["OTHER"] == "single"


def test_load_dotenv_ignores_comments_and_blanks(tmp_path: Path):
    env_file = tmp_path / ".env"
    env_file.write_text("# comment\n\nVALID=yes\n")
    result = load_dotenv(env_file)
    assert result == {"VALID": "yes"}


def test_load_dotenv_ignores_lines_without_equals(tmp_path: Path):
    env_file = tmp_path / ".env"
    env_file.write_text("NOEQUALS\nGOOD=ok\n")
    result = load_dotenv(env_file)
    assert result == {"GOOD": "ok"}


# ---------------------------------------------------------------------------
# inject_dotenv
# ---------------------------------------------------------------------------

def test_inject_dotenv_sets_vars(tmp_path: Path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("INJECT_A=1\nINJECT_B=2\n")
    monkeypatch.delenv("INJECT_A", raising=False)
    monkeypatch.delenv("INJECT_B", raising=False)
    count = inject_dotenv(env_file)
    assert count == 2
    assert os.environ["INJECT_A"] == "1"
    assert os.environ["INJECT_B"] == "2"


def test_inject_dotenv_does_not_overwrite(tmp_path: Path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("EXISTING_VAR=new_value\n")
    monkeypatch.setenv("EXISTING_VAR", "original")
    count = inject_dotenv(env_file)
    assert count == 0
    assert os.environ["EXISTING_VAR"] == "original"


# ---------------------------------------------------------------------------
# resolve_secrets
# ---------------------------------------------------------------------------

def test_resolve_secrets_braces(monkeypatch):
    monkeypatch.setenv("MY_TOKEN", "secret123")
    result = resolve_secrets({"token": "${MY_TOKEN}"})
    assert result["token"] == "secret123"


def test_resolve_secrets_no_dollar(monkeypatch):
    result = resolve_secrets({"plain": "no_expansion"})
    assert result["plain"] == "no_expansion"


def test_resolve_secrets_missing_var_raises(monkeypatch):
    monkeypatch.delenv("MISSING_SECRET", raising=False)
    with pytest.raises(KeyError, match="MISSING_SECRET"):
        resolve_secrets({"key": "${MISSING_SECRET}"})


def test_resolve_secrets_bare_dollar(monkeypatch):
    monkeypatch.setenv("BARE_VAR", "bare_value")
    result = resolve_secrets({"x": "$BARE_VAR"})
    assert result["x"] == "bare_value"
