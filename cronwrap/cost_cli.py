"""CLI rendering helpers for job cost reports."""
from __future__ import annotations

from cronwrap.cost import load_cost_log, all_job_totals, job_total_cost


def render_job_cost_report(store_dir: str, job_name: str) -> str:
    entries = [e for e in load_cost_log(store_dir) if e.job_name == job_name]
    if not entries:
        return f"No cost data found for job '{job_name}'."

    lines = [f"Cost report for '{job_name}' ({len(entries)} runs):"]
    for e in entries:
        lines.append(
            f"  {e.timestamp}  {e.duration_seconds:.2f}s  "
            f"@ {e.cost_per_second:.8f} {e.currency}/s  "
            f"= {e.total_cost:.8f} {e.currency}"
        )
    total = job_total_cost(store_dir, job_name)
    lines.append(f"  {'─' * 50}")
    lines.append(f"  Total: {total:.8f} {entries[0].currency}")
    return "\n".join(lines)


def render_all_costs(store_dir: str) -> str:
    totals = all_job_totals(store_dir)
    if not totals:
        return "No cost data recorded yet."

    lines = ["Cumulative cost by job:"]
    for job_name, total in sorted(totals.items()):
        lines.append(f"  {job_name:<40} {total:.8f} USD")
    grand = round(sum(totals.values()), 8)
    lines.append(f"  {'─' * 50}")
    lines.append(f"  Grand total: {grand:.8f} USD")
    return "\n".join(lines)


def render_cost_breakdown(store_dir: str, job_name: str, top_n: int = 5) -> str:
    entries = sorted(
        [e for e in load_cost_log(store_dir) if e.job_name == job_name],
        key=lambda e: e.total_cost,
        reverse=True,
    )[:top_n]
    if not entries:
        return f"No cost data found for job '{job_name}'."

    lines = [f"Top {top_n} most expensive runs for '{job_name}':"]
    for i, e in enumerate(entries, 1):
        lines.append(
            f"  {i}. {e.timestamp}  {e.total_cost:.8f} {e.currency}  ({e.duration_seconds:.2f}s)"
        )
    return "\n".join(lines)
