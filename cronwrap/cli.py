"""Command-line interface for cronwrap."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cronwrap.config import JobConfig
from cronwrap.runner import run_job
from cronwrap.history import load_history


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cronwrap",
        description="Lightweight wrapper that adds logging, alerting, and retry logic to any cron job.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- run subcommand ---
    run_p = subparsers.add_parser("run", help="Execute a command with cronwrap supervision.")
    run_p.add_argument("cmd", help="Shell command to run.")
    run_p.add_argument("--job-name", default="unnamed", help="Logical name for the job.")
    run_p.add_argument("--timeout", type=float, default=None, help="Timeout in seconds.")
    run_p.add_argument("--retries", type=int, default=0, help="Number of retry attempts on failure.")
    run_p.add_argument("--retry-delay", type=float, default=5.0, help="Seconds to wait between retries.")
    run_p.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                       help="Logging verbosity.")
    run_p.add_argument("--log-file", default=None, help="Optional path to a log file.")
    run_p.add_argument("--history-file", default="cronwrap_history.json",
                       help="Path to the run-history JSON file.")
    run_p.add_argument("--alert-on", nargs="*", default=["failure"],
                       choices=["failure", "success", "timeout"],
                       help="Events that trigger an alert.")

    # --- history subcommand ---
    hist_p = subparsers.add_parser("history", help="Display past run records.")
    hist_p.add_argument("--history-file", default="cronwrap_history.json",
                        help="Path to the run-history JSON file.")
    hist_p.add_argument("--job-name", default=None, help="Filter by job name.")
    hist_p.add_argument("--last", type=int, default=10, help="Show the N most recent records.")
    hist_p.add_argument("--json", dest="as_json", action="store_true",
                        help="Output records as JSON.")

    return parser


def _cmd_run(args: argparse.Namespace) -> int:
    cfg = JobConfig(
        job_name=args.job_name,
        command=args.cmd,
        timeout=args.timeout,
        retries=args.retries,
        retry_delay=args.retry_delay,
        log_level=args.log_level,
        log_file=args.log_file,
        history_file=args.history_file,
        alert_on=args.alert_on,
    )
    cfg.validate()
    record = run_job(cfg)
    return 0 if record.exit_code == 0 else 1


def _cmd_history(args: argparse.Namespace) -> int:
    records = load_history(Path(args.history_file))
    if args.job_name:
        records = [r for r in records if r.job_name == args.job_name]
    records = records[-args.last:]

    if args.as_json:
        import dataclasses
        print(json.dumps([dataclasses.asdict(r) for r in records], indent=2))
    else:
        if not records:
            print("No records found.")
        for r in records:
            status = "OK" if r.exit_code == 0 else ("TIMEOUT" if r.timed_out else "FAIL")
            print(f"{r.started_at}  {r.job_name:<20}  {status:<8}  exit={r.exit_code}  "
                  f"duration={r.duration_seconds:.2f}s")
    return 0


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command == "run":
        sys.exit(_cmd_run(args))
    elif args.command == "history":
        sys.exit(_cmd_history(args))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
