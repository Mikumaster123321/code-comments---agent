from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Callable
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


FaultInjector = Callable[[str], None]


class SQLiteCreditLedger:
    """Append-only SQLite implementation of the Phase 1 ledger contract."""

    def __init__(
        self,
        database: str | Path,
        *,
        fault_injector: FaultInjector | None = None,
    ) -> None:
        self._database = str(database)
        self._fault_injector = fault_injector
        self._lock = RLock()
        self._connection = sqlite3.connect(
            self._database,
            timeout=30,
            isolation_level=None,
            check_same_thread=False,
        )
        self._configure_connection(self._connection)
        self._initialize_schema(self._connection)

    def close(self) -> None:
        with self._lock:
            self._connection.close()

    def __enter__(self) -> SQLiteCreditLedger:
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()

    def grant(self, account_id: str, amount: int, note: str = "") -> CreditTransaction:
        account_id = normalize_account_id(account_id)
        self._validate_positive_amount(amount)
        self._validate_note(note)

        with self._write_transaction() as connection:
            return self._append_transaction(
                connection,
                account_id=account_id,
                transaction_type=TransactionType.ADMIN_GRANT,
                amount=amount,
                request_id=None,
                note=note,
            )

    def charge(
        self, account_id: str, request_id: str, amount: int, note: str = ""
    ) -> CreditTransaction:
        account_id = normalize_account_id(account_id)
        request_id = normalize_request_id(request_id)
        self._validate_positive_amount(amount)
        self._validate_note(note)

        with self._write_transaction() as connection:
            existing = self._idempotent_transaction(
                connection, TransactionType.USAGE, account_id, request_id
            )
            if existing is not None:
                return self._resolve_idempotent_retry(existing, -amount, note)
            if self._balance(connection, account_id) < amount:
                raise InsufficientCreditsError("insufficient credits")
            transaction = self._append_transaction(
                connection,
                account_id=account_id,
                transaction_type=TransactionType.USAGE,
                amount=-amount,
                request_id=request_id,
                note=note,
            )
            self._inject("after_transaction_append")
            self._append_idempotency_record(connection, transaction)
            self._inject("after_idempotency_write")
            return transaction

    def refund(
        self, account_id: str, request_id: str, amount: int, note: str = ""
    ) -> CreditTransaction:
        account_id = normalize_account_id(account_id)
        request_id = normalize_request_id(request_id)
        self._validate_positive_amount(amount)
        self._validate_note(note)

        with self._write_transaction() as connection:
            existing = self._idempotent_transaction(
                connection, TransactionType.REFUND, account_id, request_id
            )
            if existing is not None:
                return self._resolve_idempotent_retry(existing, amount, note)
            transaction = self._append_transaction(
                connection,
                account_id=account_id,
                transaction_type=TransactionType.REFUND,
                amount=amount,
                request_id=request_id,
                note=note,
            )
            self._inject("after_transaction_append")
            self._append_idempotency_record(connection, transaction)
            self._inject("after_idempotency_write")
            return transaction

    def adjust(self, account_id: str, amount: int, note: str = "") -> CreditTransaction:
        account_id = normalize_account_id(account_id)
        validate_integer_amount(amount)
        self._validate_note(note)

        with self._write_transaction() as connection:
            if self._balance(connection, account_id) + amount < 0:
                raise InsufficientCreditsError("adjustment would make balance negative")
            return self._append_transaction(
                connection,
                account_id=account_id,
                transaction_type=TransactionType.ADJUSTMENT,
                amount=amount,
                request_id=None,
                note=note,
            )

    def balance_of(self, account_id: str) -> int:
        account_id = normalize_account_id(account_id)
        with self._lock:
            return self._balance(self._connection, account_id)

    def history_of(self, account_id: str) -> tuple[CreditTransaction, ...]:
        account_id = normalize_account_id(account_id)
        with self._lock:
            rows = self._connection.execute(
                """
                SELECT transaction_id, account_id, transaction_type, amount,
                       request_id, created_at, note
                FROM credit_transactions
                WHERE account_id = ?
                ORDER BY sequence
                """,
                (account_id,),
            ).fetchall()
        return tuple(self._transaction_from_row(row) for row in rows)

    class _WriteTransaction:
        def __init__(self, ledger: SQLiteCreditLedger) -> None:
            self._ledger = ledger

        def __enter__(self) -> sqlite3.Connection:
            self._ledger._lock.acquire()
            try:
                self._ledger._connection.execute("BEGIN IMMEDIATE")
            except BaseException:
                self._ledger._lock.release()
                raise
            return self._ledger._connection

        def __exit__(self, error_type, _error, _traceback) -> bool:
            try:
                if error_type is None:
                    try:
                        self._ledger._connection.commit()
                    except BaseException:
                        self._ledger._connection.rollback()
                        raise
                else:
                    self._ledger._connection.rollback()
            finally:
                self._ledger._lock.release()
            return False

    def _write_transaction(self) -> SQLiteCreditLedger._WriteTransaction:
        return self._WriteTransaction(self)

    def _inject(self, point: str) -> None:
        if self._fault_injector is not None:
            self._fault_injector(point)

    @staticmethod
    def _configure_connection(connection: sqlite3.Connection) -> None:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 30000")

    @staticmethod
    def _initialize_schema(connection: sqlite3.Connection) -> None:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS credit_transactions (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id TEXT NOT NULL UNIQUE,
                account_id TEXT NOT NULL,
                transaction_type TEXT NOT NULL,
                amount INTEGER NOT NULL CHECK (amount != 0),
                request_id TEXT,
                created_at TEXT NOT NULL,
                note TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_credit_transactions_account
            ON credit_transactions(account_id, sequence);

            CREATE TABLE IF NOT EXISTS credit_idempotency (
                transaction_type TEXT NOT NULL,
                account_id TEXT NOT NULL,
                request_id TEXT NOT NULL,
                transaction_id TEXT NOT NULL UNIQUE,
                PRIMARY KEY (transaction_type, account_id, request_id),
                FOREIGN KEY (transaction_id)
                    REFERENCES credit_transactions(transaction_id)
                    ON DELETE RESTRICT
            );
            """
        )

    @staticmethod
    def _balance(connection: sqlite3.Connection, account_id: str) -> int:
        row = connection.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM credit_transactions WHERE account_id = ?",
            (account_id,),
        ).fetchone()
        return int(row[0])

    @classmethod
    def _append_transaction(
        cls,
        connection: sqlite3.Connection,
        *,
        account_id: str,
        transaction_type: TransactionType,
        amount: int,
        request_id: str | None,
        note: str,
    ) -> CreditTransaction:
        transaction = CreditTransaction(
            transaction_id=str(uuid4()),
            account_id=account_id,
            type=transaction_type,
            amount=amount,
            request_id=request_id,
            created_at=datetime.now(timezone.utc),
            note=note,
        )
        connection.execute(
            """
            INSERT INTO credit_transactions (
                transaction_id, account_id, transaction_type, amount,
                request_id, created_at, note
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                transaction.transaction_id,
                transaction.account_id,
                transaction.type.value,
                transaction.amount,
                transaction.request_id,
                transaction.created_at.isoformat(),
                transaction.note,
            ),
        )
        return transaction

    @staticmethod
    def _append_idempotency_record(
        connection: sqlite3.Connection, transaction: CreditTransaction
    ) -> None:
        connection.execute(
            """
            INSERT INTO credit_idempotency (
                transaction_type, account_id, request_id, transaction_id
            ) VALUES (?, ?, ?, ?)
            """,
            (
                transaction.type.value,
                transaction.account_id,
                transaction.request_id,
                transaction.transaction_id,
            ),
        )

    @classmethod
    def _idempotent_transaction(
        cls,
        connection: sqlite3.Connection,
        transaction_type: TransactionType,
        account_id: str,
        request_id: str,
    ) -> CreditTransaction | None:
        row = connection.execute(
            """
            SELECT t.transaction_id, t.account_id, t.transaction_type, t.amount,
                   t.request_id, t.created_at, t.note
            FROM credit_idempotency AS i
            JOIN credit_transactions AS t ON t.transaction_id = i.transaction_id
            WHERE i.transaction_type = ? AND i.account_id = ? AND i.request_id = ?
            """,
            (transaction_type.value, account_id, request_id),
        ).fetchone()
        return None if row is None else cls._transaction_from_row(row)

    @staticmethod
    def _transaction_from_row(row: tuple[object, ...]) -> CreditTransaction:
        return CreditTransaction(
            transaction_id=str(row[0]),
            account_id=str(row[1]),
            type=TransactionType(str(row[2])),
            amount=int(row[3]),
            request_id=None if row[4] is None else str(row[4]),
            created_at=datetime.fromisoformat(str(row[5])),
            note=str(row[6]),
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
