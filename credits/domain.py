from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class CreditError(Exception):
    """Base class for credit-domain failures."""


class InvalidAccountError(CreditError):
    """Raised when an account identifier is invalid."""


class InvalidCreditAmountError(CreditError):
    """Raised when a credit amount violates an operation contract."""


class InvalidRequestIdError(CreditError):
    """Raised when an idempotent operation has no valid request identifier."""


class InsufficientCreditsError(CreditError):
    """Raised when a debit would make an account balance negative."""


class IdempotencyConflictError(CreditError):
    """Raised when an idempotency key is reused for a different operation."""


class TransactionType(str, Enum):
    ADMIN_GRANT = "ADMIN_GRANT"
    USAGE = "USAGE"
    REFUND = "REFUND"
    ADJUSTMENT = "ADJUSTMENT"


def normalize_account_id(account_id: str) -> str:
    if not isinstance(account_id, str) or not account_id.strip():
        raise InvalidAccountError("account_id must be a non-empty string")
    return account_id.strip()


def normalize_request_id(request_id: str) -> str:
    if not isinstance(request_id, str) or not request_id.strip():
        raise InvalidRequestIdError("request_id must be a non-empty string")
    return request_id.strip()


def validate_integer_amount(amount: int) -> None:
    if not isinstance(amount, int) or isinstance(amount, bool):
        raise InvalidCreditAmountError("amount must be an integer")
    if amount == 0:
        raise InvalidCreditAmountError("amount must not be zero")


@dataclass(frozen=True)
class CreditAccount:
    account_id: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "account_id", normalize_account_id(self.account_id))


@dataclass(frozen=True)
class CreditTransaction:
    transaction_id: str
    account_id: str
    type: TransactionType
    amount: int
    request_id: Optional[str]
    created_at: datetime
    note: str

    def __post_init__(self) -> None:
        if not isinstance(self.transaction_id, str) or not self.transaction_id.strip():
            raise CreditError("transaction_id must be a non-empty string")
        object.__setattr__(self, "transaction_id", self.transaction_id.strip())
        object.__setattr__(self, "account_id", normalize_account_id(self.account_id))

        if not isinstance(self.type, TransactionType):
            raise CreditError("type must be a TransactionType")
        validate_integer_amount(self.amount)

        if self.type is TransactionType.ADMIN_GRANT and self.amount < 0:
            raise InvalidCreditAmountError("ADMIN_GRANT amount must be positive")
        if self.type is TransactionType.USAGE and self.amount > 0:
            raise InvalidCreditAmountError("USAGE amount must be negative")
        if self.type is TransactionType.REFUND and self.amount < 0:
            raise InvalidCreditAmountError("REFUND amount must be positive")

        if self.type in (TransactionType.USAGE, TransactionType.REFUND):
            object.__setattr__(self, "request_id", normalize_request_id(self.request_id))
        elif self.request_id is not None:
            if not isinstance(self.request_id, str) or not self.request_id.strip():
                raise InvalidRequestIdError("request_id must be None or a non-empty string")
            object.__setattr__(self, "request_id", self.request_id.strip())

        if not isinstance(self.created_at, datetime):
            raise CreditError("created_at must be a datetime")
        if not isinstance(self.note, str):
            raise CreditError("note must be a string")
