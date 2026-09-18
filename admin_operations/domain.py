from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from credits.domain import normalize_account_id, validate_integer_amount


class AdminOperationError(Exception):
    """Base class for trusted administrative credit-operation failures."""


class InvalidAdminOperationContextError(AdminOperationError):
    """Raised when the administrative audit context is invalid."""


class AdminOperationConflictError(AdminOperationError):
    """Raised when an operation identity is reused with a different payload."""


class AdminOperationType(str, Enum):
    GRANT = "GRANT"
    ADJUSTMENT = "ADJUSTMENT"


def _normalize_identity(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InvalidAdminOperationContextError(
            f"{field_name} must be a non-empty string"
        )
    return value.strip()


def _normalize_reason(reason: str) -> str:
    if not isinstance(reason, str) or not reason.strip():
        raise InvalidAdminOperationContextError(
            "reason must be a non-empty string"
        )
    return reason.strip()


@dataclass(frozen=True)
class AdminOperationContext:
    actor_id: str
    operation_id: str
    reason: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "actor_id", _normalize_identity(self.actor_id, "actor_id")
        )
        object.__setattr__(
            self,
            "operation_id",
            _normalize_identity(self.operation_id, "operation_id"),
        )
        object.__setattr__(self, "reason", _normalize_reason(self.reason))


@dataclass(frozen=True)
class AdminOperationRecord:
    actor_id: str
    operation_id: str
    operation_type: AdminOperationType
    account_id: str
    amount: int
    reason: str
    credit_transaction_id: str
    created_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "actor_id", _normalize_identity(self.actor_id, "actor_id")
        )
        object.__setattr__(
            self,
            "operation_id",
            _normalize_identity(self.operation_id, "operation_id"),
        )
        if not isinstance(self.operation_type, AdminOperationType):
            raise AdminOperationError("operation_type must be an AdminOperationType")
        object.__setattr__(self, "account_id", normalize_account_id(self.account_id))
        validate_integer_amount(self.amount)
        if self.operation_type is AdminOperationType.GRANT and self.amount < 0:
            raise AdminOperationError("GRANT amount must be positive")
        object.__setattr__(self, "reason", _normalize_reason(self.reason))
        if (
            not isinstance(self.credit_transaction_id, str)
            or not self.credit_transaction_id.strip()
        ):
            raise AdminOperationError(
                "credit_transaction_id must be a non-empty string"
            )
        object.__setattr__(
            self, "credit_transaction_id", self.credit_transaction_id.strip()
        )
        if not isinstance(self.created_at, datetime):
            raise AdminOperationError("created_at must be a datetime")
