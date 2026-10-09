"""Internal V3.1.4 runtime reliability contracts."""

from __future__ import annotations

from dataclasses import dataclass
import logging
import time
import uuid
from typing import Any


@dataclass(frozen=True)
class RuntimeLimits:
    """Centralized conservative intake and operation limits."""

    single_source_bytes: int = 2 * 1024 * 1024
    upload_bytes: int = 25 * 1024 * 1024
    batch_file_count: int = 200
    zip_member_count: int = 1_000
    zip_uncompressed_bytes: int = 100 * 1024 * 1024
    zip_compression_ratio: float = 100.0
    preflight_timeout_seconds: float = 6.0
    generation_timeout_seconds: float = 90.0
    javac_timeout_seconds: float = 15.0


RUNTIME_LIMITS = RuntimeLimits()
SDK_MAX_RETRIES = 0
APPLICATION_GENERATION_ATTEMPTS = 1
TRANSPORT_ATTEMPTS_PER_APPLICATION_ATTEMPT = 1


def new_operation_id() -> str:
    """Return an opaque local correlation identifier with no user data."""

    return uuid.uuid4().hex[:16]


class OperationTimer:
    """Small monotonic timer used by structured developer diagnostics."""

    def __init__(self) -> None:
        self._started = time.monotonic()

    def elapsed_ms(self) -> int:
        return max(0, round((time.monotonic() - self._started) * 1000))


_ALLOWED_DIAGNOSTIC_FIELDS = frozenset(
    {
        "operation_id",
        "stage",
        "provider_id",
        "model_id",
        "attempt",
        "duration_ms",
        "error_category",
    }
)


def log_diagnostic(logger: logging.Logger, event: str, **fields: Any) -> None:
    """Emit a redacted structured local event using an allow-list only."""

    safe_fields = {
        key: value
        for key, value in fields.items()
        if key in _ALLOWED_DIAGNOSTIC_FIELDS and value is not None
    }
    ordered = " ".join(f"{key}={safe_fields[key]}" for key in sorted(safe_fields))
    logger.info("event=%s%s", event, f" {ordered}" if ordered else "")
