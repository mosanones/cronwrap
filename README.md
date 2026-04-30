# cronwrap

Lightweight wrapper that adds logging, alerting, and retry logic to any cron job.

---

## Installation

```bash
pip install cronwrap
```

---

## Usage

Wrap any command by passing it to `cronwrap`. It will handle logging, send alerts on failure, and retry on transient errors.

```python
from cronwrap import CronWrap

job = CronWrap(
    command="python /opt/scripts/sync_data.py",
    retries=3,
    alert_email="ops@example.com",
    log_file="/var/log/cronwrap/sync_data.log"
)

job.run()
```

Or use it directly from the command line:

```bash
cronwrap --retries 3 --alert ops@example.com -- python /opt/scripts/sync_data.py
```

### Key Features

- **Logging** — Captures stdout/stderr and writes timestamped logs automatically
- **Alerting** — Sends email or webhook notifications on job failure
- **Retry logic** — Automatically retries failed jobs with configurable backoff
- **Timeout support** — Kill long-running jobs after a specified duration
- **Exit code forwarding** — Preserves the wrapped command's exit code

### Configuration

| Option | Default | Description |
|---|---|---|
| `retries` | `0` | Number of retry attempts on failure |
| `retry_delay` | `5` | Seconds to wait between retries |
| `timeout` | `None` | Max runtime in seconds before killing the job |
| `alert_email` | `None` | Email address to notify on failure |
| `log_file` | `None` | Path to write log output |

---

## License

MIT © cronwrap contributors