import os
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError, fields
from datetime import datetime, timezone
from threading import Barrier

import pytest

import admin_operations
from admin_operations import (
    AdminCreditService,
    AdminOperationConflictError,
    AdminOperationContext,
    AdminOperationRecord,
    AdminOperationType,
    InvalidAdminOperationContextError,
)
from credits import (
    CreditTransaction,
    InsufficientCreditsError,
    InvalidCreditAmountError,
    SQLiteCreditLedger,
    TransactionType,
)
from llm_provider import ModelConfig
from managed_access import (
    FlatPricingPolicy,
    LLMAccessContext,
    LLMAccessMode,
    ManagedAccessService,
)


class FailOnce:
    def __init__(self, point):
        self.point = point
        self.triggered = False

    def __call__(self, point):
        if point == self.point and not self.triggered:
            self.triggered = True
            raise sqlite3.OperationalError("injected admin sqlite failure")


class FailCommitConnection:
    def __init__(self, connection):
        self._connection = connection
        self.failed = False

    def __getattr__(self, name):
        return getattr(self._connection, name)

    def commit(self):
        if not self.failed:
            self.failed = True
            raise sqlite3.OperationalError("injected commit failure")
        return self._connection.commit()


class StubProvider:
    def invoke(self, *, model_config, prompt):
        return "safe completion"


def context(actor="admin", operation="op-1", reason="manual grant"):
    return AdminOperationContext(actor, operation, reason)


def table_count(database, table):
    with sqlite3.connect(database) as connection:
        return int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])


def database_dump(database):
    with sqlite3.connect(database) as connection:
        return "\n".join(connection.iterdump())


@pytest.mark.parametrize(
    ("actor_id", "operation_id", "reason"),
    [
        (None, "op-1", "reason"),
        (" ", "op-1", "reason"),
        ("admin", None, "reason"),
        ("admin", " ", "reason"),
        ("admin", "op-1", None),
        ("admin", "op-1", " "),
    ],
)
def test_context_requires_non_empty_actor_operation_and_reason(
    actor_id, operation_id, reason
):
    with pytest.raises(InvalidAdminOperationContextError):
        AdminOperationContext(actor_id, operation_id, reason)


def test_context_normalizes_identity_and_reason_and_is_immutable():
    operation_context = AdminOperationContext(" admin ", " op-1 ", " correction ")

    assert operation_context == AdminOperationContext("admin", "op-1", "correction")
    with pytest.raises(FrozenInstanceError):
        operation_context.reason = "changed"


def test_context_contains_no_authentication_or_runtime_objects():
    assert {field.name for field in fields(AdminOperationContext)} == {
        "actor_id",
        "operation_id",
        "reason",
    }
    assert not any(
        forbidden in field.name.lower()
        for field in fields(AdminOperationContext)
        for forbidden in ("credential", "api_key", "password", "token", "role")
    )


def test_operation_types_are_minimal_and_exclude_refund_and_payment():
    assert set(AdminOperationType) == {
        AdminOperationType.GRANT,
        AdminOperationType.ADJUSTMENT,
    }
    assert not hasattr(AdminOperationType, "REFUND")
    assert not hasattr(AdminOperationType, "PURCHASE")


def test_record_is_normalized_and_immutable():
    record = AdminOperationRecord(
        actor_id=" admin ",
        operation_id=" op-1 ",
        operation_type=AdminOperationType.GRANT,
        account_id=" alice ",
        amount=3,
        reason=" test grant ",
        credit_transaction_id=" tx-1 ",
        created_at=datetime.now(timezone.utc),
    )

    assert record.actor_id == "admin"
    assert record.operation_id == "op-1"
    assert record.account_id == "alice"
    assert record.reason == "test grant"
    with pytest.raises(FrozenInstanceError):
        record.amount = 4


def test_grant_writes_credit_and_admin_record_atomically(tmp_path):
    database = tmp_path / "admin.sqlite3"
    service = AdminCreditService(database)

    record = service.grant(context(), "account-1", 10)

    assert record.operation_type is AdminOperationType.GRANT
    assert record.account_id == "account-1"
    assert record.amount == 10
    assert service.balance("account-1") == 10
    assert service.history("account-1") == (
        CreditTransaction(
            transaction_id=record.credit_transaction_id,
            account_id="account-1",
            type=TransactionType.ADMIN_GRANT,
            amount=10,
            request_id=None,
            created_at=record.created_at,
            note="manual grant",
        ),
    )
    assert table_count(database, "admin_credit_operations") == 1


@pytest.mark.parametrize("amount", [4, -4])
def test_adjust_supports_positive_and_negative_nonzero_amounts(tmp_path, amount):
    service = AdminCreditService(tmp_path / f"adjust-{amount}.sqlite3")
    service.grant(context(operation="seed"), "account-1", 10)

    record = service.adjust(
        context(operation="adjust", reason="correction"), "account-1", amount
    )

    assert record.operation_type is AdminOperationType.ADJUSTMENT
    assert service.balance("account-1") == 10 + amount
    assert service.history("account-1")[-1].type is TransactionType.ADJUSTMENT


@pytest.mark.parametrize("amount", [0, True, False, 1.0, "1"])
def test_adjust_rejects_zero_bool_and_non_integer_amounts(tmp_path, amount):
    service = AdminCreditService(tmp_path / "admin.sqlite3")

    with pytest.raises(InvalidCreditAmountError):
        service.adjust(context(), "account-1", amount)

    assert service.balance("account-1") == 0
    assert service.history("account-1") == ()


@pytest.mark.parametrize("amount", [0, -1, True, 1.0])
def test_grant_requires_a_positive_integer(tmp_path, amount):
    service = AdminCreditService(tmp_path / "admin.sqlite3")

    with pytest.raises(InvalidCreditAmountError):
        service.grant(context(), "account-1", amount)

    assert service.balance("account-1") == 0


def test_negative_adjustment_cannot_make_balance_negative(tmp_path):
    database = tmp_path / "admin.sqlite3"
    service = AdminCreditService(database)
    seed = service.grant(context(operation="seed"), "account-1", 5)

    with pytest.raises(InsufficientCreditsError):
        service.adjust(context(operation="too-much"), "account-1", -6)

    assert service.balance("account-1") == 5
    assert service.history("account-1")[0].transaction_id == seed.credit_transaction_id
    assert table_count(database, "credit_transactions") == 1
    assert table_count(database, "admin_credit_operations") == 1


def test_exact_zero_balance_adjustment_is_allowed(tmp_path):
    service = AdminCreditService(tmp_path / "admin.sqlite3")
    service.grant(context(operation="seed"), "account-1", 5)

    service.adjust(context(operation="zero", reason="close balance"), "account-1", -5)

    assert service.balance("account-1") == 0


def test_balance_is_read_only_and_requires_no_context(tmp_path):
    database = tmp_path / "admin.sqlite3"
    service = AdminCreditService(database)

    assert service.balance(" account-1 ") == 0
    assert table_count(database, "admin_credit_operations") == 0
    assert table_count(database, "credit_transactions") == 0


def test_history_is_safe_ordered_and_immutable(tmp_path):
    service = AdminCreditService(tmp_path / "admin.sqlite3")
    service.grant(context(operation="one"), " account-1 ", 5)
    service.adjust(context(operation="two", reason="correction"), "account-1", -2)

    history = service.history(" account-1 ")

    assert isinstance(history, tuple)
    assert [transaction.amount for transaction in history] == [5, -2]
    with pytest.raises(FrozenInstanceError):
        history[0].amount = 100


def test_identical_replay_returns_original_without_duplicate_mutation(tmp_path):
    database = tmp_path / "admin.sqlite3"
    service = AdminCreditService(database)
    original = service.grant(context(), "account-1", 10)

    replay = service.grant(context(), "account-1", 10)

    assert replay == original
    assert service.balance("account-1") == 10
    assert table_count(database, "credit_transactions") == 1
    assert table_count(database, "admin_credit_operations") == 1


def test_reopen_replay_uses_persisted_admin_identity(tmp_path):
    database = tmp_path / "admin.sqlite3"
    first = AdminCreditService(database)
    original = first.grant(context(), "account-1", 10)
    first.close()

    second = AdminCreditService(database)
    replay = second.grant(context(), "account-1", 10)

    assert replay == original
    assert second.balance("account-1") == 10
    assert table_count(database, "credit_transactions") == 1


@pytest.mark.parametrize(
    ("method", "account_id", "amount", "reason"),
    [
        ("adjust", "account-1", 10, "manual grant"),
        ("grant", "account-2", 10, "manual grant"),
        ("grant", "account-1", 11, "manual grant"),
        ("grant", "account-1", 10, "different reason"),
    ],
)
def test_reused_identity_with_changed_payload_is_a_conflict(
    tmp_path, method, account_id, amount, reason
):
    database = tmp_path / "admin.sqlite3"
    service = AdminCreditService(database)
    original = service.grant(context(), "account-1", 10)

    with pytest.raises(AdminOperationConflictError):
        getattr(service, method)(context(reason=reason), account_id, amount)

    assert service.balance("account-1") == 10
    assert service.history("account-1")[0].transaction_id == original.credit_transaction_id
    assert table_count(database, "credit_transactions") == 1
    assert table_count(database, "admin_credit_operations") == 1


def test_same_operation_id_is_independent_across_actors(tmp_path):
    service = AdminCreditService(tmp_path / "admin.sqlite3")

    first = service.grant(context(actor="admin-a", operation="shared"), "account-1", 3)
    second = service.grant(context(actor="admin-b", operation="shared"), "account-1", 3)

    assert first.actor_id == "admin-a"
    assert second.actor_id == "admin-b"
    assert first.credit_transaction_id != second.credit_transaction_id
    assert service.balance("account-1") == 6


def test_account_actor_and_operation_normalization_cannot_bypass_idempotency(tmp_path):
    database = tmp_path / "admin.sqlite3"
    service = AdminCreditService(database)
    original = service.grant(
        context(actor=" admin ", operation=" op-1 "), " alice ", 7
    )

    replay = service.grant(context(actor="admin", operation="op-1"), "alice", 7)

    assert replay == original
    assert replay.account_id == "alice"
    assert table_count(database, "credit_transactions") == 1
    with sqlite3.connect(database) as connection:
        row = connection.execute(
            "SELECT actor_id, operation_id, account_id FROM admin_credit_operations"
        ).fetchone()
    assert row == ("admin", "op-1", "alice")


def test_one_hundred_replays_create_exactly_one_credit_and_admin_row(tmp_path):
    database = tmp_path / "admin.sqlite3"
    service = AdminCreditService(database)

    records = [service.grant(context(), "account-1", 9) for _ in range(100)]

    assert len(set(records)) == 1
    assert service.balance("account-1") == 9
    assert table_count(database, "credit_transactions") == 1
    assert table_count(database, "admin_credit_operations") == 1


def test_concurrent_same_operation_across_connections_mutates_once(tmp_path):
    database = tmp_path / "admin.sqlite3"
    first = AdminCreditService(database)
    second = AdminCreditService(database)
    barrier = Barrier(3)

    def grant(service):
        barrier.wait()
        return service.grant(context(), "account-1", 10)

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(grant, service) for service in (first, second)]
        barrier.wait()
        records = [future.result() for future in futures]

    assert records[0] == records[1]
    assert first.balance("account-1") == 10
    assert table_count(database, "credit_transactions") == 1
    assert table_count(database, "admin_credit_operations") == 1


def test_concurrent_different_operations_on_one_account_serialize_safely(tmp_path):
    database = tmp_path / "admin.sqlite3"
    seed = AdminCreditService(database)
    seed.grant(context(operation="seed"), "account-1", 10)
    first = AdminCreditService(database)
    second = AdminCreditService(database)
    barrier = Barrier(3)

    def grant():
        barrier.wait()
        return first.grant(context(operation="grant"), "account-1", 5)

    def adjust():
        barrier.wait()
        return second.adjust(
            context(operation="adjust", reason="correction"), "account-1", -4
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(grant), executor.submit(adjust)]
        barrier.wait()
        records = [future.result() for future in futures]

    assert {record.operation_type for record in records} == {
        AdminOperationType.GRANT,
        AdminOperationType.ADJUSTMENT,
    }
    assert seed.balance("account-1") == 11
    assert table_count(database, "credit_transactions") == 3
    assert table_count(database, "admin_credit_operations") == 3


@pytest.mark.parametrize(
    "failure_point",
    [
        "before_credit_transaction_insert",
        "after_credit_transaction_insert",
        "before_admin_operation_insert",
        "after_admin_operation_insert",
    ],
)
def test_injected_write_failures_roll_back_credit_and_admin_rows(
    tmp_path, failure_point
):
    database = tmp_path / f"{failure_point}.sqlite3"
    service = AdminCreditService(database, fault_injector=FailOnce(failure_point))

    with pytest.raises(sqlite3.OperationalError, match="injected"):
        service.grant(context(), "account-1", 10)

    assert service.balance("account-1") == 0
    assert service.history("account-1") == ()
    assert table_count(database, "credit_transactions") == 0
    assert table_count(database, "admin_credit_operations") == 0


def test_commit_failure_rolls_back_credit_and_admin_rows(tmp_path):
    database = tmp_path / "admin.sqlite3"
    service = AdminCreditService(database)
    service._connection = FailCommitConnection(service._connection)

    with pytest.raises(sqlite3.OperationalError, match="commit failure"):
        service.grant(context(), "account-1", 10)

    assert service.balance("account-1") == 0
    assert table_count(database, "credit_transactions") == 0
    assert table_count(database, "admin_credit_operations") == 0


def test_retry_after_rolled_back_failure_succeeds_safely(tmp_path):
    database = tmp_path / "admin.sqlite3"
    service = AdminCreditService(
        database, fault_injector=FailOnce("after_credit_transaction_insert")
    )

    with pytest.raises(sqlite3.OperationalError):
        service.grant(context(), "account-1", 10)
    record = service.grant(context(), "account-1", 10)

    assert record.operation_id == "op-1"
    assert service.balance("account-1") == 10
    assert table_count(database, "credit_transactions") == 1
    assert table_count(database, "admin_credit_operations") == 1


def test_admin_schema_migrates_existing_phase3_database_without_data_loss(tmp_path):
    database = tmp_path / "phase3.sqlite3"
    ledger = SQLiteCreditLedger(database)
    ledger.grant("account-1", 10, "existing grant")
    model = ModelConfig("openai", "test-model", "https://example.invalid/v1")
    managed = ManagedAccessService(database, StubProvider(), FlatPricingPolicy(3))
    managed.invoke(
        LLMAccessContext(LLMAccessMode.MANAGED, model, "account-1", "request-1"),
        "offline prompt",
    )
    managed.close()
    ledger.close()

    service = AdminCreditService(database)

    assert service.balance("account-1") == 7
    assert [transaction.type for transaction in service.history("account-1")] == [
        TransactionType.ADMIN_GRANT,
        TransactionType.USAGE,
    ]
    assert table_count(database, "managed_requests") == 1
    assert table_count(database, "managed_usage") == 1
    assert table_count(database, "admin_credit_operations") == 0


def test_admin_schema_migration_is_idempotent_across_reopens(tmp_path):
    database = tmp_path / "admin.sqlite3"
    first = AdminCreditService(database)
    original = first.grant(context(), "account-1", 6)
    first.close()

    for _ in range(5):
        reopened = AdminCreditService(database)
        assert reopened.grant(context(), "account-1", 6) == original
        reopened.close()

    assert table_count(database, "credit_transactions") == 1
    assert table_count(database, "admin_credit_operations") == 1


def test_admin_schema_migration_failure_rolls_back_and_reopen_recovers(tmp_path):
    database = tmp_path / "admin.sqlite3"
    ledger = SQLiteCreditLedger(database)
    ledger.grant("account-1", 5, "existing")
    ledger.close()

    with pytest.raises(sqlite3.OperationalError, match="injected"):
        AdminCreditService(
            database, fault_injector=FailOnce("before_admin_schema_commit")
        )

    with sqlite3.connect(database) as connection:
        admin_schema = connection.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type = 'table' AND name = 'admin_credit_operations'
            """
        ).fetchone()
    assert admin_schema is None
    assert table_count(database, "credit_transactions") == 1

    reopened = AdminCreditService(database)
    assert reopened.balance("account-1") == 5
    assert table_count(database, "admin_credit_operations") == 0


def test_admin_audit_foreign_key_rejects_missing_credit_transaction(tmp_path):
    database = tmp_path / "admin.sqlite3"
    service = AdminCreditService(database)
    service.close()

    with sqlite3.connect(database) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO admin_credit_operations (
                    actor_id, operation_id, operation_type, account_id,
                    amount, reason, credit_transaction_id, created_at
                ) VALUES ('admin', 'op-1', 'GRANT', 'account-1', 1,
                          'reason', 'missing', '2026-01-01T00:00:00+00:00')
                """
            )

    assert table_count(database, "admin_credit_operations") == 0


def test_public_surface_exposes_no_refund_or_ledger(tmp_path):
    service = AdminCreditService(tmp_path / "admin.sqlite3")

    assert not hasattr(service, "refund")
    assert not hasattr(service, "ledger")
    assert "CreditLedger" not in admin_operations.__all__
    assert "SQLiteCreditLedger" not in admin_operations.__all__


def test_managed_surface_does_not_expose_admin_operations():
    for name in ("grant", "adjust", "refund", "ledger", "admin_service"):
        assert not hasattr(ManagedAccessService, name)


def test_reason_is_business_audit_data_and_is_persisted(tmp_path):
    database = tmp_path / "admin.sqlite3"
    service = AdminCreditService(database)
    service.grant(context(reason="CUSTOM_BUSINESS_REASON"), "account-1", 2)

    dump = database_dump(database)

    assert dump.count("CUSTOM_BUSINESS_REASON") == 2


def test_admin_service_never_touches_provider_credentials(tmp_path, monkeypatch):
    database = tmp_path / "admin.sqlite3"
    marker = "TEST_ADMIN_SECRET_UNIQUE"
    monkeypatch.setenv("OPENAI_API_KEY", marker)
    service = AdminCreditService(database)
    operation_context = context(reason="ordinary audit reason")
    service.grant(operation_context, "account-1", 4)

    with pytest.raises(AdminOperationConflictError) as captured:
        service.adjust(operation_context, "account-1", 4)
    service_repr = repr(service)
    service.close()

    with sqlite3.connect(database) as connection:
        rows = repr(connection.execute("SELECT * FROM admin_credit_operations").fetchall())
        credit_rows = repr(connection.execute("SELECT * FROM credit_transactions").fetchall())
    dump = database_dump(database)
    raw = database.read_bytes()
    sidecars = b"".join(
        path.read_bytes()
        for path in (
            database.with_name(database.name + "-journal"),
            database.with_name(database.name + "-wal"),
            database.with_name(database.name + "-shm"),
        )
        if path.exists()
    )

    assert os.environ["OPENAI_API_KEY"] == marker
    assert marker not in rows
    assert marker not in credit_rows
    assert marker not in dump
    assert marker.encode() not in raw
    assert marker.encode() not in sidecars
    assert marker not in service_repr
    assert marker not in repr(captured.value)
