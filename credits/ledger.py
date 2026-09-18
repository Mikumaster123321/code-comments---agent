from __future__ import annotations

from datetime import datetime, timezone
from threading import RLock
from typing import Protocol
from uuid import uuid4

from .domain import (
    CreditError,
    CreditTransaction,
    IdempotencyConflictError,
    InsufficientCreditsError,
    InvalidCreditAmountError,
    TransactionType,
    normalize_account_id,
    normalize_request_id,
    validate_integer_amount,
)


class CreditLedger(Protocol):
    def grant(self, account_id: str, amount: int, note: str = "") -> CreditTransaction: ...

    def charge(
        self, account_id: str, request_id: str, amount: int, note: str = ""
    ) -> CreditTransaction: ...

    def refund(
        self, account_id: str, request_id: str, amount: int, note: str = ""
    ) -> CreditTransaction: ...

    def adjust(self, account_id: str, amount: int, note: str = "") -> CreditTransaction: ...

    def balance_of(self, account_id: str) -> int: ...

    def history_of(self, account_id: str) -> tuple[CreditTransaction, ...]: ...


class InMemoryCreditLedger:
    def __init__(self) -> None:
        self._transactions: list[CreditTransaction] = []
        self._idempotency_index: dict[
            tuple[TransactionType, str, str], CreditTransaction
        ] = {}
        self._lock = RLock()

    def grant(self, account_id: str, amount: int, note: str = "") -> CreditTransaction:
        account_id = normalize_account_id(account_id)
        self._validate_positive_amount(amount)
        self._validate_note(note)
        with self._lock:
            transaction = self._new_transaction(
                account_id=account_id,
                transaction_type=TransactionType.ADMIN_GRANT,
                amount=amount,
                request_id=None,
                note=note,
            )
            self._transactions.append(transaction)
            return transaction

    def charge(
        self, account_id: str, request_id: str, amount: int, note: str = ""
    ) -> CreditTransaction:
        account_id = normalize_account_id(account_id)
        request_id = normalize_request_id(request_id)
        self._validate_positive_amount(amount)
        self._validate_note(note)
        key = (TransactionType.USAGE, account_id, request_id)

        with self._lock:
            existing = self._idempotency_index.get(key)
            if existing is not None:
                return self._resolve_idempotent_retry(existing, -amount, note)
            if self._balance_unlocked(account_id) < amount:
                raise InsufficientCreditsError("insufficient credits")

            transaction = self._new_transaction(
                account_id=account_id,
                transaction_type=TransactionType.USAGE,
                amount=-amount,
                request_id=request_id,
                note=note,
            )
            self._transactions.append(transaction)
            self._idempotency_index[key] = transaction
            return transaction

    def refund(
        self, account_id: str, request_id: str, amount: int, note: str = ""
    ) -> CreditTransaction:
        account_id = normalize_account_id(account_id)
        request_id = normalize_request_id(request_id)
        self._validate_positive_amount(amount)
        self._validate_note(note)
        key = (TransactionType.REFUND, account_id, request_id)

        with self._lock:
            existing = self._idempotency_index.get(key)
            if existing is not None:
                return self._resolve_idempotent_retry(existing, amount, note)

            transaction = self._new_transaction(
                account_id=account_id,
                transaction_type=TransactionType.REFUND,
                amount=amount,
                request_id=request_id,
                note=note,
            )
            self._transactions.append(transaction)
            self._idempotency_index[key] = transaction
            return transaction

    def adjust(self, account_id: str, amount: int, note: str = "") -> CreditTransaction:
        account_id = normalize_account_id(account_id)
        validate_integer_amount(amount)
        self._validate_note(note)
        with self._lock:
            if self._balance_unlocked(account_id) + amount < 0:
                raise InsufficientCreditsError("adjustment would make balance negative")
            transaction = self._new_transaction(
                account_id=account_id,
                transaction_type=TransactionType.ADJUSTMENT,
                amount=amount,
                request_id=None,
                note=note,
            )
            self._transactions.append(transaction)
            return transaction

    def balance_of(self, account_id: str) -> int:
        account_id = normalize_account_id(account_id)
        with self._lock:
            return self._balance_unlocked(account_id)

    def history_of(self, account_id: str) -> tuple[CreditTransaction, ...]:
        account_id = normalize_account_id(account_id)
        with self._lock:
            return tuple(
                transaction
                for transaction in self._transactions
                if transaction.account_id == account_id
            )

    def _balance_unlocked(self, account_id: str) -> int:
        return sum(
            transaction.amount
            for transaction in self._transactions
            if transaction.account_id == account_id
        )

    @staticmethod
    def _validate_positive_amount(amount: int) -> None:
        validate_integer_amount(amount)
        if amount < 0:
            raise InvalidCreditAmountError("amount must be positive")

    @staticmethod
    def _validate_note(note: str) -> None:
        if not isinstance(note, str):
            raise CreditError("note must be a string")

    @staticmethod
    def _resolve_idempotent_retry(
        existing: CreditTransaction, amount: int, note: str
    ) -> CreditTransaction:
        if existing.amount != amount or existing.note != note:
            raise IdempotencyConflictError(
                "idempotency key was already used with different parameters"
            )
        return existing

    @staticmethod
    def _new_transaction(
        *,
        account_id: str,
        transaction_type: TransactionType,
        amount: int,
        request_id: str | None,
        note: str,
    ) -> CreditTransaction:
        return CreditTransaction(
            transaction_id=str(uuid4()),
            account_id=account_id,
            type=transaction_type,
            amount=amount,
            request_id=request_id,
            created_at=datetime.now(timezone.utc),
            note=note,
        )
