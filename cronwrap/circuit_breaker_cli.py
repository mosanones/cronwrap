"""CLI helpers for inspecting circuit-breaker state."""
from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from typing import List

from cronwrap.circuit_breaker import CircuitState, load_state, _state_path

_ICONS = {"closed": "✅", "open": "🔴", "half-open": "🟡"}


def _all_job_names(store_dir: str) -> List[str]:
    if not os.path.isdir(store_dir):
        return []
    names = []
    for fname in sorted(os.listdir(store_dir)):
        if fname.endswith(".circuit.json"):
            names.append(fname[: -len(".circuit.json")])
    return names


def render_circuit_state(state: CircuitState, now_ts: float = 0.0) -> str:
    icon = _ICONS.get(state.state, "❓")
    lines = [
        f"{icon}  {state.job_name}  [{state.state.upper()}]",
        f"   consecutive failures : {state.consecutive_failures}",
    ]
    if state.opened_at:
        opened_dt = datetime.fromisoformat(state.opened_at)
        elapsed = int((now_ts or time.time()) - opened_dt.timestamp())
        lines.append(f"   opened at            : {state.opened_at}  ({elapsed}s ago)")
    return "\n".join(lines)


def render_all_circuits(store_dir: str) -> str:
    names = _all_job_names(store_dir)
    if not names:
        return "No circuit-breaker state found."
    now_ts = time.time()
    blocks = [render_circuit_state(load_state(store_dir, n), now_ts) for n in names]
    return "\n\n".join(blocks)


def render_open_circuits(store_dir: str) -> str:
    names = _all_job_names(store_dir)
    now_ts = time.time()
    open_states = [
        load_state(store_dir, n)
        for n in names
        if load_state(store_dir, n).state == "open"
    ]
    if not open_states:
        return "No open circuits."
    blocks = [render_circuit_state(s, now_ts) for s in open_states]
    return "\n\n".join(blocks)
