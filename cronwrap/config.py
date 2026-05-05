"""Configuration dataclass for a cronwrap job."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class JobConfig:
    """Holds all runtime settings for a wrapped cron job."""

    # Required
    command: str
    name: str = "cron-job"

    # Retry settings
    retries: int = 1
    retry_delay: float = 5.0
    retry_backoff: float = 2.0

    # Execution settings
    timeout: Optional[int] = None

    # Alerting
    alert_on_failure: bool = True
    alert_on_success: bool = False
    alert_emails: List[str] = field(default_factory=list)

    # Logging
    log_file: Optional[str] = None
    log_level: str = "INFO"

    def validate(self) -> None:
        """Raise ValueError for invalid configurations."""
        if not self.command:
            raise ValueError("command must not be empty")
        if self.retries < 1:
            raise ValueError("retries must be >= 1")
        if self.retry_delay < 0:
            raise ValueError("retry_delay must be >= 0")
        if self.retry_backoff < 1:
            raise ValueError("retry_backoff must be >= 1")
        if self.timeout is not None and self.timeout <= 0:
            raise ValueError("timeout must be a positive integer")
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if self.log_level.upper() not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        if self.alert_emails and not self.alert_on_failure and not self.alert_on_success:
            raise ValueError(
                "alert_emails is set but both alert_on_failure and alert_on_success are False"
            )

    def effective_log_level(self) -> str:
        """Return the normalised (uppercase) log level string."""
        return self.log_level.upper()
