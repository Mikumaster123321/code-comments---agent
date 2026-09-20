import sqlite3
from concurrent.futures import ThreadPoolExecutor
from dataclasses import fields
from decimal import Decimal
from threading import Event

import pytest

from credits import InsufficientCreditsError, SQLiteCreditLedger, TransactionType
from llm_provider import ModelConfig, RuntimeCredential
from managed_access import (
    FlatPricingPolicy,
    LLMAccessContext,
    LLMAccessMode,
    ManagedAccessResult,
    ManagedAccessService,
    ManagedFinalizationError,
    ManagedProviderResponse,
    ManagedRequestConflictError,
    ManagedRequestRecoveryRequiredError,
    ManagedRequestStatus,
    PricingContext,
    TokenPricingPolicy,
    UsageRecord,
)


MODEL = ModelConfig("openai", "test-model", "https://example.invalid/v1")
LIMITS = PricingContext("openai", "test-model", 3000, 2000)
POLICY = TokenPricingPolicy(Decimal("1"), Decimal("2"))


class StubProvider:
    def __init__(self, response, *, entered=None, release=None, secret=None):
        self.response = response
        self.calls = []
        self.entered = entered
        self.release = release
        self.credential = RuntimeCredential(secret) if secret else None

    def invoke(self, *, model_config, prompt):
        self.calls.append((model_config, prompt))
        if self.entered is not None:
            self.entered.set()
        if self.release is not None:
            assert self.release.wait(timeout=5)
        return self.response


class FailOnce:
    def __init__(self, point):
        self.point = point
        self.triggered = False

    def __call__(self, point):
        if point == self.point and not self.triggered:
            self.triggered = True
            raise sqlite3.OperationalError("injected phase 3 failure")


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
            raise sqlite3.OperationalError("injected phase 3 commit failure")
        return self._connection.commit()


class UnderReservingPolicy:
    policy_id = "test-under-reserving:v1"

    def reserve_credits(self, context):
        return 1

    def price_usage(self, context, usage):
        return 2


def context(request_id="request-1"):
    return LLMAccessContext(
        LLMAccessMode.MANAGED,
        MODEL,
        account_id="account-1",
        request_id=request_id,
    )


def response(input_tokens=1000, output_tokens=500, provider_id="openai", model="test-model"):
    return ManagedProviderResponse(
        "safe completion",
        UsageRecord(provider_id, model, input_tokens, output_tokens),
    )


def malformed_response():
    value = ManagedProviderResponse("completion", None)
    object.__setattr__(value, "usage", object())
    return value


def funded_database(tmp_path, amount=10):
    database = tmp_path / "managed-token.sqlite3"
    ledger = SQLiteCreditLedger(database)
    ledger.grant("account-1", amount, "test grant")
    return database, ledger


def counts(database):
    with sqlite3.connect(database) as connection:
        return {
            table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in ("credit_transactions", "credit_idempotency", "managed_usage")
        }


def test_token_flow_charges_actual_usage_releases_difference_and_persists(tmp_path):
    database, ledger = funded_database(tmp_path)
    provider = StubProvider(response())
    service = ManagedAccessService(database, provider, POLICY)

    result = service.invoke(context(), "prompt", pricing_context=LIMITS)

    assert result.credits_charged == 2
    assert result.usage == response().usage
    assert ledger.balance_of("account-1") == 8
    assert ledger.history_of("account-1")[-1].amount == -2
    assert service.get_request("account-1", "request-1").reserved_credits == 7
    with sqlite3.connect(database) as connection:
        assert connection.execute(
            """
            SELECT provider_id, model, input_tokens, output_tokens, final_credits
            FROM managed_usage
            """
        ).fetchone() == ("openai", "test-model", 1000, 500, 2)


def test_token_flow_equal_reservation_charges_once(tmp_path):
    database, ledger = funded_database(tmp_path)
    provider = StubProvider(response(3000, 2000))
    service = ManagedAccessService(database, provider, POLICY)

    result = service.invoke(context(), "prompt", pricing_context=LIMITS)

    assert result.credits_charged == 7
    assert ledger.balance_of("account-1") == 3


def test_zero_rate_usage_succeeds_without_creating_zero_credit_transaction(tmp_path):
    database, ledger = funded_database(tmp_path)
    policy = TokenPricingPolicy(Decimal("1"), Decimal("0"))
    limits = PricingContext("openai", "test-model", 1000, 1000)
    provider = StubProvider(response(0, 100))
    service = ManagedAccessService(database, provider, policy)

    result = service.invoke(context(), "prompt", pricing_context=limits)

    assert result.credits_charged == 0
    assert ledger.balance_of("account-1") == 10
    assert [item.type for item in ledger.history_of("account-1")].count(
        TransactionType.USAGE
    ) == 0
    with sqlite3.connect(database) as connection:
        assert connection.execute(
            "SELECT final_credits FROM managed_usage"
        ).fetchone()[0] == 0


def test_succeeded_token_request_replays_persisted_usage_after_restart(tmp_path):
    database, ledger = funded_database(tmp_path)
    first_provider = StubProvider(response())
    first = ManagedAccessService(database, first_provider, POLICY)
    first.invoke(context(), "prompt", pricing_context=LIMITS)
    first.close()

    replay_provider = StubProvider(response(1, 1))
    reopened = ManagedAccessService(database, replay_provider, POLICY)
    replay = reopened.invoke(context(), "prompt", pricing_context=LIMITS)

    assert replay == ManagedAccessResult(
        request_id="request-1",
        account_id="account-1",
        status=ManagedRequestStatus.SUCCEEDED,
        credits_charged=2,
        replayed=True,
        content=None,
        usage=UsageRecord("openai", "test-model", 1000, 500),
    )
    assert replay_provider.calls == []
    assert ledger.balance_of("account-1") == 8


@pytest.mark.parametrize(
    "provider_response",
    [
        ManagedProviderResponse("completion", None),
        malformed_response(),
        response(provider_id="other"),
        response(model="other"),
        response(input_tokens=3001, output_tokens=0),
    ],
)
def test_missing_invalid_or_inconsistent_usage_fails_closed(
    tmp_path, provider_response
):
    database, ledger = funded_database(tmp_path, amount=7)
    provider = StubProvider(provider_response)
    service = ManagedAccessService(database, provider, POLICY)

    with pytest.raises(ManagedFinalizationError, match="usage requires reconciliation"):
        service.invoke(context(), "prompt", pricing_context=LIMITS)

    assert len(provider.calls) == 1
    assert service.get_request("account-1", "request-1").status is ManagedRequestStatus.FINALIZATION_FAILED
    assert ledger.balance_of("account-1") == 7
    assert counts(database) == {
        "credit_transactions": 1,
        "credit_idempotency": 0,
        "managed_usage": 0,
    }
    with pytest.raises(ManagedFinalizationError, match="already succeeded"):
        service.invoke(context(), "prompt", pricing_context=LIMITS)
    assert len(provider.calls) == 1


def test_actual_above_reservation_is_never_charged(tmp_path):
    database, ledger = funded_database(tmp_path)
    provider = StubProvider(response())
    service = ManagedAccessService(database, provider, UnderReservingPolicy())

    with pytest.raises(ManagedFinalizationError):
        service.invoke(context(), "prompt", pricing_context=LIMITS)

    assert ledger.balance_of("account-1") == 10
    assert service.get_request("account-1", "request-1").status is ManagedRequestStatus.FINALIZATION_FAILED
    assert len(provider.calls) == 1


def test_token_reservation_requires_available_upper_bound_before_provider(tmp_path):
    database, ledger = funded_database(tmp_path, amount=6)
    provider = StubProvider(response())
    service = ManagedAccessService(database, provider, POLICY)

    with pytest.raises(InsufficientCreditsError):
        service.invoke(context(), "prompt", pricing_context=LIMITS)

    assert provider.calls == []
    assert ledger.balance_of("account-1") == 6


def test_different_token_reservations_prevent_concurrent_overspend(tmp_path):
    database, ledger = funded_database(tmp_path, amount=7)
    entered = Event()
    release = Event()
    provider = StubProvider(response(), entered=entered, release=release)
    service = ManagedAccessService(database, provider, POLICY)

    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(
            service.invoke, context("request-1"), "first", pricing_context=LIMITS
        )
        assert entered.wait(timeout=5)
        with pytest.raises(InsufficientCreditsError):
            service.invoke(context("request-2"), "second", pricing_context=LIMITS)
        release.set()
        assert first.result(timeout=5).credits_charged == 2

    assert len(provider.calls) == 1
    assert ledger.balance_of("account-1") == 5


def test_two_services_same_token_request_call_provider_once(tmp_path):
    database, ledger = funded_database(tmp_path)
    entered = Event()
    release = Event()
    first_provider = StubProvider(response(), entered=entered, release=release)
    second_provider = StubProvider(response())
    first = ManagedAccessService(database, first_provider, POLICY)
    second = ManagedAccessService(database, second_provider, POLICY)

    with ThreadPoolExecutor(max_workers=2) as executor:
        pending = executor.submit(
            first.invoke, context(), "prompt", pricing_context=LIMITS
        )
        assert entered.wait(timeout=5)
        with pytest.raises(ManagedRequestRecoveryRequiredError):
            second.invoke(context(), "prompt", pricing_context=LIMITS)
        release.set()
        assert pending.result(timeout=5).credits_charged == 2

    assert len(first_provider.calls) + len(second_provider.calls) == 1
    assert ledger.balance_of("account-1") == 8


def test_reserved_token_request_survives_restart_without_provider_retry(tmp_path):
    database, ledger = funded_database(tmp_path, amount=7)
    provider = StubProvider(response())
    first = ManagedAccessService(
        database,
        provider,
        POLICY,
        fault_injector=FailOnce("after_reservation_commit"),
    )
    with pytest.raises(ManagedRequestRecoveryRequiredError):
        first.invoke(context(), "prompt", pricing_context=LIMITS)
    first.close()

    replay_provider = StubProvider(response())
    reopened = ManagedAccessService(database, replay_provider, POLICY)
    with pytest.raises(ManagedRequestRecoveryRequiredError):
        reopened.invoke(context(), "prompt", pricing_context=LIMITS)
    with pytest.raises(InsufficientCreditsError):
        reopened.invoke(context("request-2"), "other", pricing_context=LIMITS)

    assert provider.calls == replay_provider.calls == []
    assert ledger.balance_of("account-1") == 7


@pytest.mark.parametrize(
    "failure_point",
    [
        "before_usage_metadata_write",
        "after_usage_metadata_write",
        "before_usage_append",
        "after_usage_append_before_idempotency_commit",
        "before_request_success_update",
        "before_request_final_status_commit",
    ],
)
def test_token_finalization_failures_are_atomic_and_non_retriable(
    tmp_path, failure_point
):
    database, ledger = funded_database(tmp_path)
    provider = StubProvider(response())
    service = ManagedAccessService(
        database, provider, POLICY, fault_injector=FailOnce(failure_point)
    )

    with pytest.raises(ManagedFinalizationError):
        service.invoke(context(), "prompt", pricing_context=LIMITS)

    assert service.get_request("account-1", "request-1").status is ManagedRequestStatus.FINALIZATION_FAILED
    assert ledger.balance_of("account-1") == 10
    assert counts(database) == {
        "credit_transactions": 1,
        "credit_idempotency": 0,
        "managed_usage": 0,
    }
    with pytest.raises(ManagedFinalizationError):
        service.invoke(context(), "prompt", pricing_context=LIMITS)
    assert len(provider.calls) == 1


def test_token_finalization_commit_failure_rolls_back_everything(tmp_path):
    database, ledger = funded_database(tmp_path)
    provider = StubProvider(response())
    service = ManagedAccessService(database, provider, POLICY)
    service._connection = FailCommitConnection(service._connection, fail_on_commit=2)

    with pytest.raises(ManagedFinalizationError):
        service.invoke(context(), "prompt", pricing_context=LIMITS)

    assert service.get_request("account-1", "request-1").status is ManagedRequestStatus.FINALIZATION_FAILED
    assert ledger.balance_of("account-1") == 10
    assert counts(database) == {
        "credit_transactions": 1,
        "credit_idempotency": 0,
        "managed_usage": 0,
    }
    assert len(provider.calls) == 1


def test_pricing_inputs_and_policy_identity_are_part_of_request_identity(tmp_path):
    database, _ledger = funded_database(tmp_path)
    first = ManagedAccessService(database, StubProvider(response()), POLICY)
    first.invoke(context(), "prompt", pricing_context=LIMITS)
    first.close()

    changed_limits = ManagedAccessService(database, StubProvider(response()), POLICY)
    with pytest.raises(ManagedRequestConflictError):
        changed_limits.invoke(
            context(),
            "prompt",
            pricing_context=PricingContext("openai", "test-model", 2999, 2000),
        )
    changed_policy = ManagedAccessService(
        database,
        StubProvider(response()),
        TokenPricingPolicy(Decimal("1.1"), Decimal("2")),
    )
    with pytest.raises(ManagedRequestConflictError):
        changed_policy.invoke(context(), "prompt", pricing_context=LIMITS)


def test_phase_2_schema_is_migrated_and_existing_data_replays(tmp_path):
    database = tmp_path / "phase2.sqlite3"
    ledger = SQLiteCreditLedger(database)
    ledger.grant("account-1", 10, "grant")
    ledger.charge("account-1", "request-1", 4, "managed access usage")
    prompt = "legacy prompt"
    legacy_hash = ManagedAccessService._legacy_payload_hash(MODEL, prompt, 4)
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
        connection.execute(
            """
            INSERT INTO managed_requests VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "account-1",
                "request-1",
                MODEL.provider_id,
                MODEL.model,
                MODEL.base_url,
                4,
                "SUCCEEDED",
                legacy_hash,
            ),
        )

    provider = StubProvider("unused")
    service = ManagedAccessService(database, provider, FlatPricingPolicy(4))
    replay = service.invoke(context(), prompt)

    assert replay.replayed is True
    assert replay.credits_charged == 4
    assert provider.calls == []
    assert ledger.balance_of("account-1") == 6
    with sqlite3.connect(database) as connection:
        columns = {
            row[1] for row in connection.execute("PRAGMA table_info(managed_requests)")
        }
        assert {
            "pricing_policy_id",
            "payload_version",
            "max_input_tokens",
            "max_output_tokens",
        } <= columns
        assert connection.execute("SELECT COUNT(*) FROM managed_usage").fetchone()[0] == 1


def test_usage_schema_and_public_types_are_private_and_credential_free(tmp_path):
    secret = "sk-fake-phase3-only-secret"
    database, _ledger = funded_database(tmp_path)
    provider = StubProvider(response(), secret=secret)
    service = ManagedAccessService(database, provider, POLICY)
    result = service.invoke(context(), "private prompt", pricing_context=LIMITS)
    request = service.get_request("account-1", "request-1")

    for value in (response().usage, LIMITS, response(), request, result, service):
        assert secret not in repr(value)
    for domain_type in (UsageRecord, PricingContext, ManagedProviderResponse):
        names = {item.name.lower() for item in fields(domain_type)}
        assert names.isdisjoint(
            {"credential", "api_key", "prompt", "completion", "raw_request", "raw_response", "client"}
        )
    with sqlite3.connect(database) as connection:
        columns = {
            row[1]
            for table in ("managed_requests", "managed_usage")
            for row in connection.execute(f"PRAGMA table_info({table})")
        }
    assert columns.isdisjoint(
        {"credential", "api_key", "prompt", "completion", "raw_request", "raw_response", "client"}
    )
    payload = database.read_bytes()
    assert secret.encode() not in payload
    assert b"private prompt" not in payload
    assert b"safe completion" not in payload
