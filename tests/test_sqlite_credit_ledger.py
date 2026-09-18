import sqlite3
from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError
from decimal import Decimal
from threading import Barrier

import pytest

from credits import (
    CreditTransaction,
    IdempotencyConflictError,
    InsufficientCreditsError,
    InvalidAccountError,
    InvalidCreditAmountError,
    InvalidRequestIdError,
    SQLiteCreditLedger,
    TransactionType,
)


class FailOnce:
    def __init__(self, point):
        self.point = point
        self.triggered = False

    def __call__(self, point):
        if point == self.point and not self.triggered:
            self.triggered = True
            raise sqlite3.OperationalError("injected sqlite failure")


def table_count(database, table):
    with sqlite3.connect(database) as connection:
        return connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def test_schema_initialization_is_minimal_and_complete(tmp_path):
    database = tmp_path / "credits.sqlite3"
    ledger = SQLiteCreditLedger(database)
    ledger.close()

    with sqlite3.connect(database) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }

    assert {"credit_transactions", "credit_idempotency"} <= tables


def test_empty_valid_account_has_zero_balance_and_history(tmp_path):
    ledger = SQLiteCreditLedger(tmp_path / "credits.sqlite3")

    assert ledger.balance_of("account-1") == 0
    assert ledger.history_of("account-1") == ()


def test_grant_charge_refund_and_adjust_persist(tmp_path):
    ledger = SQLiteCreditLedger(tmp_path / "credits.sqlite3")

    grant = ledger.grant("account-1", 20, "grant")
    usage = ledger.charge("account-1", "usage-1", 7, "usage")
    refund = ledger.refund("account-1", "refund-1", 2, "refund")
    adjustment = ledger.adjust("account-1", -3, "adjustment")

    assert [item.type for item in ledger.history_of("account-1")] == [
        TransactionType.ADMIN_GRANT,
        TransactionType.USAGE,
        TransactionType.REFUND,
        TransactionType.ADJUSTMENT,
    ]
    assert ledger.history_of("account-1") == (grant, usage, refund, adjustment)
    assert ledger.balance_of("account-1") == 12


def test_reopen_preserves_balance_history_and_idempotency(tmp_path):
    database = tmp_path / "credits.sqlite3"
    ledger = SQLiteCreditLedger(database)
    grant = ledger.grant("account-1", 10)
    usage = ledger.charge("account-1", "usage-1", 4, "analysis")
    ledger.close()

    reopened = SQLiteCreditLedger(database)

    assert reopened.balance_of("account-1") == 6
    assert reopened.history_of("account-1") == (grant, usage)
    assert reopened.charge("account-1", "usage-1", 4, "analysis") == usage
    assert len(reopened.history_of("account-1")) == 2


def test_all_operations_normalize_account_and_request_ids(tmp_path):
    ledger = SQLiteCreditLedger(tmp_path / "credits.sqlite3")
    ledger.grant(" alice ", 10)
    usage = ledger.charge("alice", " request-1 ", 3)
    refund = ledger.refund("\talice\n", " refund-1 ", 1)
    ledger.adjust(" alice ", -2)

    assert usage.account_id == refund.account_id == "alice"
    assert usage.request_id == "request-1"
    assert refund.request_id == "refund-1"
    assert ledger.balance_of(" alice ") == 6
    assert len(ledger.history_of("\talice\n")) == 4


@pytest.mark.parametrize("operation", ["charge", "refund"])
def test_idempotent_replay_returns_equal_original_without_new_row(tmp_path, operation):
    ledger = SQLiteCreditLedger(tmp_path / "credits.sqlite3")
    ledger.grant("account-1", 10)

    original = getattr(ledger, operation)("account-1", " request-1 ", 3, "note")
    replay = getattr(ledger, operation)(" account-1 ", "request-1", 3, "note")

    assert replay == original
    assert len(ledger.history_of("account-1")) == 2


@pytest.mark.parametrize("operation", ["charge", "refund"])
@pytest.mark.parametrize(
    ("amount", "note"),
    [(4, "note"), (3, "different")],
)
def test_idempotency_payload_conflict_has_no_state_change(
    tmp_path, operation, amount, note
):
    ledger = SQLiteCreditLedger(tmp_path / "credits.sqlite3")
    ledger.grant("account-1", 10)
    original = getattr(ledger, operation)("account-1", "request-1", 3, "note")

    with pytest.raises(IdempotencyConflictError):
        getattr(ledger, operation)("account-1", "request-1", amount, note)

    assert ledger.history_of("account-1") == (
        ledger.history_of("account-1")[0],
        original,
    )


def test_usage_and_refund_keep_independent_idempotency_namespaces(tmp_path):
    ledger = SQLiteCreditLedger(tmp_path / "credits.sqlite3")
    ledger.grant("account-1", 10)

    usage = ledger.charge("account-1", "request-1", 3, "usage")
    refund = ledger.refund("account-1", "request-1", 2, "refund")

    assert ledger.charge("account-1", "request-1", 3, "usage") == usage
    assert ledger.refund("account-1", "request-1", 2, "refund") == refund


def test_negative_balance_operations_are_rejected_atomically(tmp_path):
    ledger = SQLiteCreditLedger(tmp_path / "credits.sqlite3")
    grant = ledger.grant("account-1", 5)

    with pytest.raises(InsufficientCreditsError):
        ledger.charge("account-1", "usage-1", 6)
    with pytest.raises(InsufficientCreditsError):
        ledger.adjust("account-1", -6)

    assert ledger.balance_of("account-1") == 5
    assert ledger.history_of("account-1") == (grant,)


@pytest.mark.parametrize("amount", [0, -1, True, 1.0, Decimal("1")])
def test_credit_amounts_remain_positive_integers_and_reject_bool(tmp_path, amount):
    ledger = SQLiteCreditLedger(tmp_path / "credits.sqlite3")

    with pytest.raises(InvalidCreditAmountError):
        ledger.grant("account-1", amount)

    assert ledger.history_of("account-1") == ()


def test_invalid_account_request_and_note_match_in_memory_contract(tmp_path):
    ledger = SQLiteCreditLedger(tmp_path / "credits.sqlite3")

    with pytest.raises(InvalidAccountError):
        ledger.balance_of(" ")
    with pytest.raises(InvalidRequestIdError):
        ledger.charge("account-1", " ", 1)
    with pytest.raises(Exception, match="note must be a string"):
        ledger.grant("account-1", 1, None)


def test_history_is_ordered_and_transactions_are_immutable(tmp_path):
    ledger = SQLiteCreditLedger(tmp_path / "credits.sqlite3")
    transactions = [ledger.grant("account-1", 1) for _ in range(3)]

    history = ledger.history_of("account-1")

    assert history == tuple(transactions)
    assert isinstance(history, tuple)
    with pytest.raises(FrozenInstanceError):
        history[0].amount = 2


@pytest.mark.parametrize(
    "failure_point", ["after_transaction_append", "after_idempotency_write"]
)
def test_usage_failure_rolls_back_transaction_and_idempotency_together(
    tmp_path, failure_point
):
    database = tmp_path / "credits.sqlite3"
    injector = FailOnce(failure_point)
    ledger = SQLiteCreditLedger(database, fault_injector=injector)
    grant = ledger.grant("account-1", 10)

    with pytest.raises(sqlite3.OperationalError, match="injected"):
        ledger.charge("account-1", "usage-1", 4, "usage")

    assert ledger.history_of("account-1") == (grant,)
    assert ledger.balance_of("account-1") == 10
    assert table_count(database, "credit_transactions") == 1
    assert table_count(database, "credit_idempotency") == 0


@pytest.mark.parametrize(
    "failure_point", ["after_transaction_append", "after_idempotency_write"]
)
def test_refund_failure_leaves_no_orphan_transaction_or_index(
    tmp_path, failure_point
):
    database = tmp_path / "credits.sqlite3"
    ledger = SQLiteCreditLedger(database, fault_injector=FailOnce(failure_point))

    with pytest.raises(sqlite3.OperationalError, match="injected"):
        ledger.refund("account-1", "refund-1", 4, "refund")

    assert ledger.history_of("account-1") == ()
    assert table_count(database, "credit_transactions") == 0
    assert table_count(database, "credit_idempotency") == 0


def test_retry_after_rolled_back_failure_can_succeed(tmp_path):
    database = tmp_path / "credits.sqlite3"
    injector = FailOnce("after_transaction_append")
    ledger = SQLiteCreditLedger(database, fault_injector=injector)
    ledger.grant("account-1", 10)

    with pytest.raises(sqlite3.OperationalError):
        ledger.charge("account-1", "usage-1", 4)

    transaction = ledger.charge("account-1", "usage-1", 4)
    assert transaction.type is TransactionType.USAGE
    assert ledger.balance_of("account-1") == 6


def test_foreign_key_prevents_an_orphan_idempotency_record(tmp_path):
    database = tmp_path / "credits.sqlite3"
    ledger = SQLiteCreditLedger(database)
    ledger.close()

    with sqlite3.connect(database) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO credit_idempotency
                    (transaction_type, account_id, request_id, transaction_id)
                VALUES ('USAGE', 'account-1', 'request-1', 'missing')
                """
            )

    assert table_count(database, "credit_idempotency") == 0


def test_concurrent_overspend_is_prevented_across_connections(tmp_path):
    database = tmp_path / "credits.sqlite3"
    first = SQLiteCreditLedger(database)
    second = SQLiteCreditLedger(database)
    first.grant("account-1", 10)
    barrier = Barrier(3)

    def charge(ledger, request_id):
        barrier.wait()
        try:
            return ledger.charge("account-1", request_id, 8)
        except InsufficientCreditsError as error:
            return error

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(charge, first, "one"),
            executor.submit(charge, second, "two"),
        ]
        barrier.wait()
        outcomes = [future.result() for future in futures]

    assert sum(isinstance(item, CreditTransaction) for item in outcomes) == 1
    assert sum(isinstance(item, InsufficientCreditsError) for item in outcomes) == 1
    assert first.balance_of("account-1") == 2
    assert [item.type for item in first.history_of("account-1")].count(
        TransactionType.USAGE
    ) == 1
