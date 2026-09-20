from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from threading import RLock
from typing import Callable

from credits import CreditTransaction, InsufficientCreditsError, TransactionType
from credits.domain import (
    InvalidCreditAmountError,
    validate_integer_amount,
)
from credits.sqlite_ledger import SQLiteCreditLedger

from .domain import (
    AdminOperationConflictError,
    AdminOperationContext,
    AdminOperationRecord,
    AdminOperationType,
    normalize_admin_account_id,
)


FaultInjector = Callable[[str], None]
_SQLITE_INTEGER_MIN = -(2**63)
_SQLITE_INTEGER_MAX = 2**63 - 1


class AdminCreditService:
    """Trusted server-side boundary for persistent administrative Credits changes."""

    def __init__(
        self,
        database: str | Path,
        *,
        fault_injector: FaultInjector | None = None,
    ) -> None:
        self._fault_injector = fault_injector
        self._lock = RLock()
        self._connection = sqlite3.connect(
            str(database),
            timeout=30,
            isolation_level=None,
            check_same_thread=False,
        )
        SQLiteCreditLedger._configure_connection(self._connection)
        try:
            SQLiteCreditLedger._initialize_schema(self._connection)
            self._initialize_schema()
        except BaseException:
            self._connection.close()
            raise

    def __repr__(self) -> str:
        return "AdminCreditService(<trusted server-side boundary>)"

    def close(self) -> None:
        with self._lock:
            self._connection.close()

    def __enter__(self) -> AdminCreditService:
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()

    def grant(
        self,
        context: AdminOperationContext,
        account_id: str,
        amount: int,
    ) -> AdminOperationRecord:
        context = self._validate_context(context)
        account_id = normalize_admin_account_id(account_id)
        self._validate_positive_amount(amount)
        return self._apply(
            context=context,
            operation_type=AdminOperationType.GRANT,
            account_id=account_id,
            amount=amount,
        )

    def adjust(
        self,
        context: AdminOperationContext,
        account_id: str,
        amount: int,
    ) -> AdminOperationRecord:
        context = self._validate_context(context)
        account_id = normalize_admin_account_id(account_id)
        self._validate_sqlite_amount(amount)
        return self._apply(
            context=context,
            operation_type=AdminOperationType.ADJUSTMENT,
            account_id=account_id,
            amount=amount,
        )

    def balance(self, account_id: str) -> int:
        account_id = normalize_admin_account_id(account_id)
        with self._lock:
            return SQLiteCreditLedger._balance(self._connection, account_id)

    def history(self, account_id: str) -> tuple[CreditTransaction, ...]:
        account_id = normalize_admin_account_id(account_id)
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
        return tuple(SQLiteCreditLedger._transaction_from_row(row) for row in rows)

    def _apply(
        self,
        *,
        context: AdminOperationContext,
        operation_type: AdminOperationType,
        account_id: str,
        amount: int,
    ) -> AdminOperationRecord:
        with self._write_transaction() as connection:
            row = self._operation_row(
                connection, context.actor_id, context.operation_id
            )
            if row is not None:
                record = self._record_from_row(row)
                self._validate_replay(
                    record,
                    operation_type=operation_type,
                    account_id=account_id,
                    amount=amount,
                    reason=context.reason,
                )
                return record

            if (
                operation_type is AdminOperationType.ADJUSTMENT
                and SQLiteCreditLedger._balance(connection, account_id) + amount < 0
            ):
                raise InsufficientCreditsError(
                    "adjustment would make balance negative"
                )

            transaction_type = (
                TransactionType.ADMIN_GRANT
                if operation_type is AdminOperationType.GRANT
                else TransactionType.ADJUSTMENT
            )
            self._inject("before_credit_transaction_insert")
            transaction = SQLiteCreditLedger._append_transaction(
                connection,
                account_id=account_id,
                transaction_type=transaction_type,
                amount=amount,
                request_id=None,
                note=context.reason,
            )
            self._inject("after_credit_transaction_insert")

            record = AdminOperationRecord(
                actor_id=context.actor_id,
                operation_id=context.operation_id,
                operation_type=operation_type,
                account_id=account_id,
                amount=amount,
                reason=context.reason,
                credit_transaction_id=transaction.transaction_id,
                created_at=transaction.created_at,
            )
            self._inject("before_admin_operation_insert")
            connection.execute(
                """
                INSERT INTO admin_credit_operations (
                    actor_id, operation_id, operation_type, account_id,
                    amount, reason, credit_transaction_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.actor_id,
                    record.operation_id,
                    record.operation_type.value,
                    record.account_id,
                    record.amount,
                    record.reason,
                    record.credit_transaction_id,
                    record.created_at.isoformat(),
                ),
            )
            self._inject("after_admin_operation_insert")
            return record

    def _initialize_schema(self) -> None:
        with self._write_transaction() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS admin_credit_operations (
                    actor_id TEXT NOT NULL CHECK (length(trim(actor_id)) > 0),
                    operation_id TEXT NOT NULL CHECK (length(trim(operation_id)) > 0),
                    operation_type TEXT NOT NULL CHECK (
                        operation_type IN ('GRANT', 'ADJUSTMENT')
                    ),
                    account_id TEXT NOT NULL CHECK (length(trim(account_id)) > 0),
                    amount INTEGER NOT NULL CHECK (
                        (operation_type = 'GRANT' AND amount > 0)
                        OR (operation_type = 'ADJUSTMENT' AND amount != 0)
                    ),
                    reason TEXT NOT NULL CHECK (length(trim(reason)) > 0),
                    credit_transaction_id TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (actor_id, operation_id),
                    FOREIGN KEY (credit_transaction_id)
                        REFERENCES credit_transactions(transaction_id)
                        ON DELETE RESTRICT
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_admin_credit_operations_account
                ON admin_credit_operations(account_id, created_at)
                """
            )
            self._inject("before_admin_schema_commit")

    class _WriteTransaction:
        def __init__(self, service: AdminCreditService) -> None:
            self._service = service

        def __enter__(self) -> sqlite3.Connection:
            self._service._lock.acquire()
            try:
                self._service._connection.execute("BEGIN IMMEDIATE")
            except BaseException:
                self._service._lock.release()
                raise
            return self._service._connection

        def __exit__(self, error_type, _error, _traceback) -> bool:
            try:
                if error_type is None:
                    try:
                        self._service._connection.commit()
                    except BaseException:
                        self._service._connection.rollback()
                        raise
                else:
                    self._service._connection.rollback()
            finally:
                self._service._lock.release()
            return False

    def _write_transaction(self) -> AdminCreditService._WriteTransaction:
        return self._WriteTransaction(self)

    def _inject(self, point: str) -> None:
        if self._fault_injector is not None:
            self._fault_injector(point)

    @staticmethod
    def _operation_row(
        connection: sqlite3.Connection, actor_id: str, operation_id: str
    ) -> tuple[object, ...] | None:
        return connection.execute(
            """
            SELECT actor_id, operation_id, operation_type, account_id,
                   amount, reason, credit_transaction_id, created_at
            FROM admin_credit_operations
            WHERE actor_id = ? AND operation_id = ?
            """,
            (actor_id, operation_id),
        ).fetchone()

    @staticmethod
    def _record_from_row(row: tuple[object, ...]) -> AdminOperationRecord:
        return AdminOperationRecord(
            actor_id=str(row[0]),
            operation_id=str(row[1]),
            operation_type=AdminOperationType(str(row[2])),
            account_id=str(row[3]),
            amount=int(row[4]),
            reason=str(row[5]),
            credit_transaction_id=str(row[6]),
            created_at=datetime.fromisoformat(str(row[7])),
        )

    @staticmethod
    def _validate_replay(
        record: AdminOperationRecord,
        *,
        operation_type: AdminOperationType,
        account_id: str,
        amount: int,
        reason: str,
    ) -> None:
        if (
            record.operation_type is not operation_type
            or record.account_id != account_id
            or record.amount != amount
            or record.reason != reason
        ):
            raise AdminOperationConflictError(
                "operation_id was already used with a different payload"
            )

    @staticmethod
    def _validate_context(context: AdminOperationContext) -> AdminOperationContext:
        if not isinstance(context, AdminOperationContext):
            raise TypeError("context must be an AdminOperationContext")
        return context

    @staticmethod
    def _validate_positive_amount(amount: int) -> None:
        AdminCreditService._validate_sqlite_amount(amount)
        if amount < 0:
            raise InvalidCreditAmountError("amount must be positive")

    @staticmethod
    def _validate_sqlite_amount(amount: int) -> None:
        validate_integer_amount(amount)
        if not _SQLITE_INTEGER_MIN <= amount <= _SQLITE_INTEGER_MAX:
            raise InvalidCreditAmountError(
                "amount must fit SQLite's signed 64-bit INTEGER range"
            )
