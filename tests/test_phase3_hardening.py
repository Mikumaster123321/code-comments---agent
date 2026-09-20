import sqlite3
from decimal import Decimal
from pathlib import Path

import pytest

from credits import InsufficientCreditsError, SQLiteCreditLedger
from llm_provider import ModelConfig, RuntimeCredential
from managed_access import (
    FlatPricingPolicy,
    LLMAccessContext,
    LLMAccessMode,
    ManagedAccessService,
    ManagedFinalizationError,
    ManagedProviderResponse,
    ManagedRequestConflictError,
    ManagedRequestFailedError,
    ManagedRequestRecoveryRequiredError,
    ManagedRequestStatus,
    PricingContext,
    TokenPricingPolicy,
    UsageRecord,
)


MODEL = ModelConfig("openai", "test-model", "https://example.invalid/v1")
LIMITS = PricingContext("openai", "test-model", 3000, 2000)
TOKEN_POLICY = TokenPricingPolicy(Decimal("1"), Decimal("2"))
USAGE_NOTE = "managed access usage"


class StubProvider:
    def __init__(self, response, *, secret=None):
        self.response = response
        self.calls = []
        self.credential = RuntimeCredential(secret) if secret is not None else None

    def invoke(self, *, model_config, prompt):
        self.calls.append((model_config, prompt))
        return self.response


class FailOnce:
    def __init__(self, point):
        self.point = point
        self.triggered = False

    def __call__(self, point):
        if point == self.point and not self.triggered:
            self.triggered = True
            raise sqlite3.OperationalError("injected Phase 3.1 failure")


class FailCommitConnection:
    def __init__(self, connection, fail_on_commit):
        self._connection = connection
        self._fail_on_commit = fail_on_commit
        self.commit_calls = 0

    def __getattr__(self, name):
        return getattr(self._connection, name)

    def commit(self):
        self.commit_calls += 1
        if self.commit_calls == self._fail_on_commit:
            raise sqlite3.OperationalError("injected Phase 3.1 commit failure")
        return self._connection.commit()


class UnderReservingPolicy:
    policy_id = "phase3.1-under-reserving:v1"

    def reserve_credits(self, context):
        return 1

    def price_usage(self, context, usage):
        return 2


def managed_context(request_id="request-1"):
    return LLMAccessContext(
        LLMAccessMode.MANAGED,
        MODEL,
        account_id="account-1",
        request_id=request_id,
    )


def token_response(content="completion", *, provider_id="openai", model="test-model"):
    return ManagedProviderResponse(
        content,
        UsageRecord(provider_id, model, 1000, 500),
    )


def build_phase2_database(database, *, succeeded_prompt="phase2-success-prompt"):
    ledger = SQLiteCreditLedger(database)
    grant = ledger.grant("account-1", 40, "phase2 grant")
    usage = ledger.charge(
        "account-1", "succeeded-request", 4, USAGE_NOTE
    )
    expected_history = ledger.history_of("account-1")
    expected_balance = ledger.balance_of("account-1")
    ledger.close()

    rows = (
        (
            "account-1",
            "succeeded-request",
            MODEL.provider_id,
            MODEL.model,
            MODEL.base_url,
            4,
            "SUCCEEDED",
            ManagedAccessService._legacy_payload_hash(
                MODEL, succeeded_prompt, 4
            ),
        ),
        (
            "account-1",
            "failed-request",
            MODEL.provider_id,
            MODEL.model,
            MODEL.base_url,
            3,
            "FAILED",
            ManagedAccessService._legacy_payload_hash(
                MODEL, "phase2-failed-prompt", 3
            ),
        ),
        (
            "account-1",
            "reserved-request",
            MODEL.provider_id,
            MODEL.model,
            MODEL.base_url,
            7,
            "RESERVED",
            ManagedAccessService._legacy_payload_hash(
                MODEL, "phase2-reserved-prompt", 7
            ),
        ),
    )
    with sqlite3.connect(database) as connection:
        connection.execute(
            """
            CREATE TABLE managed_requests (
                account_id TEXT NOT NULL,
                request_id TEXT NOT NULL,
                provider_id TEXT NOT NULL,
                model TEXT NOT NULL,
                base_url TEXT NOT NULL,
                reserved_credits INTEGER NOT NULL CHECK (reserved_credits > 0),
                status TEXT NOT NULL,
                payload_hash TEXT NOT NULL,
                PRIMARY KEY (account_id, request_id)
            )
            """
        )
        connection.executemany(
            "INSERT INTO managed_requests VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            rows,
        )
    return grant, usage, expected_history, expected_balance


def schema_snapshot(database):
    with sqlite3.connect(database) as connection:
        tables = tuple(
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
            )
        )
        columns = tuple(
            row[1]
            for row in connection.execute("PRAGMA table_info(managed_requests)")
        )
        requests = tuple(
            connection.execute(
                "SELECT * FROM managed_requests ORDER BY request_id"
            ).fetchall()
        )
        usage = (
            tuple(
                connection.execute(
                    "SELECT * FROM managed_usage ORDER BY request_id"
                ).fetchall()
            )
            if "managed_usage" in tables
            else None
        )
    return tables, columns, requests, usage


def test_real_phase2_schema_migration_preserves_ledger_idempotency_and_states(tmp_path):
    database = tmp_path / "real-phase2.sqlite3"
    _grant, original_usage, expected_history, expected_balance = build_phase2_database(
        database
    )

    succeeded_provider = StubProvider("unused")
    service = ManagedAccessService(database, succeeded_provider, FlatPricingPolicy(4))
    replay = service.invoke(
        managed_context("succeeded-request"), "phase2-success-prompt"
    )

    assert replay.replayed is True
    assert replay.credits_charged == 4
    assert succeeded_provider.calls == []
    assert service.get_request("account-1", "succeeded-request").status is ManagedRequestStatus.SUCCEEDED
    assert service.get_request("account-1", "failed-request").status is ManagedRequestStatus.FAILED
    assert service.get_request("account-1", "reserved-request").status is ManagedRequestStatus.RESERVED

    ledger = SQLiteCreditLedger(database)
    assert ledger.balance_of("account-1") == expected_balance
    assert ledger.history_of("account-1") == expected_history
    assert ledger.charge(
        "account-1", "succeeded-request", 4, USAGE_NOTE
    ) == original_usage
    assert ledger.history_of("account-1") == expected_history

    failed_provider = StubProvider("unused")
    failed = ManagedAccessService(database, failed_provider, FlatPricingPolicy(3))
    with pytest.raises(ManagedRequestFailedError):
        failed.invoke(managed_context("failed-request"), "phase2-failed-prompt")
    reserved_provider = StubProvider("unused")
    reserved = ManagedAccessService(database, reserved_provider, FlatPricingPolicy(7))
    with pytest.raises(ManagedRequestRecoveryRequiredError):
        reserved.invoke(
            managed_context("reserved-request"), "phase2-reserved-prompt"
        )
    with pytest.raises(InsufficientCreditsError):
        ManagedAccessService(
            database, StubProvider("unused"), FlatPricingPolicy(30)
        ).invoke(managed_context("new-request"), "new")

    assert failed_provider.calls == reserved_provider.calls == []
    with sqlite3.connect(database) as connection:
        assert connection.execute(
            "SELECT request_id, final_credits FROM managed_usage"
        ).fetchall() == [("succeeded-request", 4)]


def test_migrated_database_reopens_five_times_without_data_drift(tmp_path):
    database = tmp_path / "idempotent-migration.sqlite3"
    build_phase2_database(database)
    ManagedAccessService(database, StubProvider("unused"), FlatPricingPolicy(4)).close()
    expected = schema_snapshot(database)

    for _ in range(5):
        ManagedAccessService(
            database, StubProvider("unused"), FlatPricingPolicy(4)
        ).close()
        assert schema_snapshot(database) == expected


@pytest.mark.parametrize(
    "failure_point",
    [
        "after_first_schema_alteration",
        "during_migration_backfill",
        "before_managed_usage_creation",
        "during_legacy_usage_initialization",
    ],
)
def test_real_sqlite_migration_failure_rolls_back_all_ddl_and_data(
    tmp_path, failure_point
):
    database = tmp_path / f"rollback-{failure_point}.sqlite3"
    _grant, _usage, expected_history, expected_balance = build_phase2_database(database)
    old_snapshot = schema_snapshot(database)

    with pytest.raises(sqlite3.OperationalError, match="injected Phase 3.1 failure"):
        ManagedAccessService(
            database,
            StubProvider("unused"),
            FlatPricingPolicy(4),
            fault_injector=FailOnce(failure_point),
        )

    assert schema_snapshot(database) == old_snapshot
    ledger = SQLiteCreditLedger(database)
    assert ledger.balance_of("account-1") == expected_balance
    assert ledger.history_of("account-1") == expected_history
    ledger.close()

    recovered = ManagedAccessService(
        database, StubProvider("unused"), FlatPricingPolicy(4)
    )
    recovered.close()
    tables, columns, requests, usage = schema_snapshot(database)
    assert "managed_usage" in tables
    assert len(columns) == 12
    assert len(requests) == 3
    assert len(usage) == 1


def test_migration_insert_or_ignore_preserves_existing_usage_metadata(tmp_path):
    database = tmp_path / "usage-preservation.sqlite3"
    build_phase2_database(database)
    ManagedAccessService(database, StubProvider("unused"), FlatPricingPolicy(4)).close()
    expected = ("openai", "test-model", 123, 456, 4)
    with sqlite3.connect(database) as connection:
        connection.execute(
            """
            UPDATE managed_usage
            SET provider_id = ?, model = ?, input_tokens = ?, output_tokens = ?,
                final_credits = ?
            WHERE account_id = ? AND request_id = ?
            """,
            (*expected, "account-1", "succeeded-request"),
        )

    for _ in range(5):
        ManagedAccessService(
            database, StubProvider("unused"), FlatPricingPolicy(4)
        ).close()

    with sqlite3.connect(database) as connection:
        assert connection.execute(
            """
            SELECT provider_id, model, input_tokens, output_tokens, final_credits
            FROM managed_usage
            WHERE account_id = ? AND request_id = ?
            """,
            ("account-1", "succeeded-request"),
        ).fetchone() == expected


def _new_funded_database(database):
    ledger = SQLiteCreditLedger(database)
    ledger.grant("account-1", 10, "test grant")
    return ledger


@pytest.mark.parametrize("failure_mode", ["status-update", "commit"])
def test_zero_cost_finalization_failure_has_no_orphan_usage_and_keeps_reservation(
    tmp_path, failure_mode
):
    database = tmp_path / f"zero-cost-{failure_mode}.sqlite3"
    ledger = _new_funded_database(database)
    policy = TokenPricingPolicy(Decimal("1"), Decimal("0"))
    limits = PricingContext("openai", "test-model", 1000, 1000)
    provider = StubProvider(
        ManagedProviderResponse(
            "completion", UsageRecord("openai", "test-model", 0, 100)
        )
    )
    injector = FailOnce("before_request_success_update") if failure_mode == "status-update" else None
    service = ManagedAccessService(
        database, provider, policy, fault_injector=injector
    )
    if failure_mode == "commit":
        service._connection = FailCommitConnection(
            service._connection, fail_on_commit=2
        )

    with pytest.raises(ManagedFinalizationError):
        service.invoke(managed_context(), "prompt", pricing_context=limits)

    assert service.get_request("account-1", "request-1").status is ManagedRequestStatus.FINALIZATION_FAILED
    assert ledger.balance_of("account-1") == 10
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT COUNT(*) FROM managed_usage").fetchone()[0] == 0
        assert connection.execute("SELECT COUNT(*) FROM credit_idempotency").fetchone()[0] == 0
    with pytest.raises(ManagedFinalizationError):
        service.invoke(managed_context(), "prompt", pricing_context=limits)
    with pytest.raises(InsufficientCreditsError):
        ManagedAccessService(
            database, StubProvider("unused"), FlatPricingPolicy(10)
        ).invoke(managed_context("replacement"), "replacement")
    assert len(provider.calls) == 1


@pytest.mark.parametrize("first_mode", ["flat", "token"])
def test_same_request_conflicts_between_flat_and_token_pricing(tmp_path, first_mode):
    database = tmp_path / f"flat-token-{first_mode}.sqlite3"
    ledger = _new_funded_database(database)
    prompt = "same prompt"
    if first_mode == "flat":
        first_provider = StubProvider("completion")
        first = ManagedAccessService(database, first_provider, FlatPricingPolicy(4))
        first.invoke(managed_context(), prompt)
        second_provider = StubProvider(token_response())
        second = ManagedAccessService(database, second_provider, TOKEN_POLICY)
        invoke = lambda: second.invoke(
            managed_context(), prompt, pricing_context=LIMITS
        )
    else:
        first_provider = StubProvider(token_response())
        first = ManagedAccessService(database, first_provider, TOKEN_POLICY)
        first.invoke(managed_context(), prompt, pricing_context=LIMITS)
        second_provider = StubProvider("completion")
        second = ManagedAccessService(database, second_provider, FlatPricingPolicy(4))
        invoke = lambda: second.invoke(managed_context(), prompt)

    with pytest.raises(ManagedRequestConflictError):
        invoke()

    assert len(first_provider.calls) == 1
    assert second_provider.calls == []
    assert len(ledger.history_of("account-1")) == 2


def _assert_markers_absent(database, markers):
    with sqlite3.connect(database) as connection:
        tables = tuple(
            row[0]
            for row in connection.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
                """
            )
        )
        logical = "\n".join(
            repr(connection.execute(f'SELECT * FROM "{table}"').fetchall())
            for table in tables
        ).encode()
        dump = "\n".join(connection.iterdump()).encode()
    for marker in markers:
        encoded = marker.encode()
        assert encoded not in logical
        assert encoded not in dump
        for suffix in ("", "-journal", "-wal", "-shm"):
            path = Path(f"{database}{suffix}")
            if path.exists():
                assert encoded not in path.read_bytes()


def test_privacy_markers_never_enter_success_failure_or_migration_storage(tmp_path):
    prompt_marker = "PHASE31-UNIQUE-PROMPT-MARKER"
    completion_marker = "PHASE31-UNIQUE-COMPLETION-MARKER"
    secret_marker = "sk-phase31-unique-secret-marker"
    markers = (prompt_marker, completion_marker, secret_marker)
    databases = []

    scenarios = (
        ("success", TOKEN_POLICY, token_response(completion_marker), None),
        (
            "missing",
            TOKEN_POLICY,
            ManagedProviderResponse(completion_marker, None),
            None,
        ),
        (
            "mismatch",
            TOKEN_POLICY,
            token_response(completion_marker, model="other-model"),
            None,
        ),
        (
            "over-reservation",
            UnderReservingPolicy(),
            token_response(completion_marker),
            None,
        ),
        (
            "finalization",
            TOKEN_POLICY,
            token_response(completion_marker),
            FailOnce("after_usage_metadata_write"),
        ),
    )
    for name, policy, provider_response, injector in scenarios:
        database = tmp_path / f"privacy-{name}.sqlite3"
        databases.append(database)
        ledger = _new_funded_database(database)
        provider = StubProvider(provider_response, secret=secret_marker)
        service = ManagedAccessService(
            database, provider, policy, fault_injector=injector
        )
        try:
            service.invoke(
                managed_context(), prompt_marker, pricing_context=LIMITS
            )
        except ManagedFinalizationError:
            pass
        service.close()
        ledger.close()

    migration_database = tmp_path / "privacy-migration.sqlite3"
    databases.append(migration_database)
    build_phase2_database(
        migration_database, succeeded_prompt=prompt_marker
    )
    migration_provider = StubProvider(completion_marker, secret=secret_marker)
    migrated = ManagedAccessService(
        migration_database, migration_provider, FlatPricingPolicy(4)
    )
    migrated.invoke(managed_context("succeeded-request"), prompt_marker)
    migrated.close()

    for database in databases:
        _assert_markers_absent(database, markers)
