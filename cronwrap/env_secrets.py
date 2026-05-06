"""Resolve secret values from environment variables or .env files."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Dict, Optional

# Pattern: ${ENV_VAR_NAME} or $ENV_VAR_NAME
_ENV_REF_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}|\$([A-Za-z_][A-Za-z0-9_]*)")


def load_dotenv(path: Path) -> Dict[str, str]:
    """Parse a .env file and return a dict of key/value pairs.

    Lines starting with '#' and blank lines are ignored.
    Values may optionally be quoted with single or double quotes.
    """
    env: Dict[str, str] = {}
    if not path.exists():
        return env
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        # Strip surrounding quotes
        if len(value) >= 2 and value[0] in ('"', "'") and value[-1] == value[0]:
            value = value[1:-1]
        env[key] = value
    return env


def inject_dotenv(path: Optional[Path] = None) -> int:
    """Load a .env file into os.environ (existing vars are NOT overwritten).

    Returns the number of variables injected.
    """
    resolved = path or Path(".env")
    pairs = load_dotenv(resolved)
    injected = 0
    for k, v in pairs.items():
        if k not in os.environ:
            os.environ[k] = v
            injected += 1
    return injected


def resolve_secrets(mapping: Dict[str, str]) -> Dict[str, str]:
    """Expand ${VAR} / $VAR references inside *values* of *mapping*.

    Raises KeyError if a referenced variable is absent from os.environ.
    """
    result: Dict[str, str] = {}
    for key, template in mapping.items():
        def _replace(m: re.Match) -> str:  # noqa: E306
            var = m.group(1) or m.group(2)
            if var not in os.environ:
                raise KeyError(f"Environment variable '{var}' is not set")
            return os.environ[var]
        result[key] = _ENV_REF_RE.sub(_replace, template)
    return result
