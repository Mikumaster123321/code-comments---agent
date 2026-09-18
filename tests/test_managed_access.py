import sqlite3
from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError, fields
from threading import Event

import pytest

from credits import InsufficientCreditsError, SQLiteCreditLedger, TransactionType
from llm_provider import ModelConfig, RuntimeCredential
from managed_access import (
    FlatPricingPolicy,
    InvalidAccessContextError,
    InvalidFlatPricingError,
    LLMAccessContext,
    LLMAccessMode,
    ManagedAccessError,
    ManagedAccessResult,
    ManagedAccessService,
    ManagedFinalizationError,
    ManagedProviderError,
    ManagedRequest,
    ManagedRequestConflictError,
    ManagedRequestFailedError,
    ManagedRequestRecoveryRequiredError,
    ManagedRequestStatus,
)


MODEL = ModelConfig("openai", "test-model", "https://example.invalid/v1")


class StubProvider:
    def __init__(self, *, error=None, entered=None, release=None, output="completion"):
        self.calls = []
        self.error = error
        self.entered = entered
        self.release = release
        self.output = output

    def invoke(self, *, model_config, prompt):
        self.calls.append((model_config, prompt))
        if self.entered is not None:
            self.entered.set()
        if self.release is not None:
            assert self.release.wait(timeout=5)
        if self.error is not None:
            raise self.error
        return self.output


class FailOnce:
    def __init__(self, point):
        self.point = point
        self.triggered = False

    def __call__(self, point):
        if point == self.point and not self.triggered:
            self.triggered = True
            raise sqlite3.OperationalError("injected managed sqlite failure")


def managed_context(account_id="account-1", request_id="request-1", model=MODEL):
    return LLMAccessContext(
        mode=LLMAccessMode.MANAGED,
        model_config=model,
        account_id=account_id,
        request_id=request_id,
    )


def funded_database(tmp_path, *, accounts=("account-1",), amount=10):
    database = tmp_path / "managed.sqlite3"
    ledger = SQLiteCreditLedger(database)
    for account_id in accounts:
        ledger.grant(account_id, amount, "test grant")
    return database, ledger


@pytest.mark.parametrize(
    ("account_id", "request_id"),
    [(None, "request-1"), (" ", "request-1"), ("account-1", None), ("account-1", " ")],
)
def test_managed_context_requires_account_and_request(account_id, request_id):
    with pytest.raises(InvalidAccessContextError):
        managed_context(account_id, request_id)


def test_managed_context_normalizes_identity_and_is_immutable():
    context = managed_context(" account-1 ", " request-1 ")

    assert context.account_id == "account-1"
    assert context.request_id == "request-1"
    with pytest.raises(FrozenInstanceError):
        context.request_id = "other"


def test_byok_context_remains_optional_and_credential_free():
    context = LLMAccessContext(LLMAccessMode.BYOK, MODEL)

    assert context.account_id is None
    assert context.request_id is None
    assert {item.name for item in fields(context)} == {
        "mode",
        "model_config",
        "account_id",
        "request_id",
    }
    assert not any(
        forbidden in item.name.lower()
        for item in fields(context)
        for forbidden in ("credential", "api_key", "client", "provider")
    )


@pytest.mark.parametrize("credits", [0, -1, True, False, 1.0, "1"])
def test_flat_pricing_requires_positive_integer_and_rejects_bool(credits):
    with pytest.raises(InvalidFlatPricingError):
        FlatPricingPolicy(credits)


def test_flat_pricing_is_known_before_provider_invocation():
    policy = FlatPricingPolicy(7)

    assert policy.credits_for(MODEL) == 7


def test_managed_request_is_immutable_and_contains_no_runtime_objects():
    request = ManagedRequest(
        request_id="request-1",
        account_id="account-1",
        model_config=MODEL,
        reserved_credits=4,
        status=ManagedRequestStatus.RESERVED,
    )

    assert {item.name for item in fields(request)} == {
        "request_id",
        "account_id",
        "model_config",
        "reserved_credits",
        "status",
    }
    with pytest.raises(FrozenInstanceError):
        request.status = ManagedRequestStatus.SUCCEEDED


def test_insufficient_credits_does_not_reserve_or_call_provider(tmp_path):
    database, ledger = funded_database(tmp_path, amount=3)
    provider = StubProvider()
    service = ManagedAccessService(database, provider, FlatPricingPolicy(4))

    with pytest.raises(InsufficientCreditsError):
        service.invoke(managed_context(), "prompt")

    assert provider.calls == []
    assert service.get_request("account-1", "request-1") is None
    assert ledger.balance_of("account-1") == 3


def test_reservation_is_persisted_before_provider_and_does_not_charge(tmp_path):
    database, ledger = funded_database(tmp_path)
    entered = Event()
    release = Event()
    provider = StubProvider(entered=entered, release=release)
    service = ManagedAccessService(database, provider, FlatPricingPolicy(4))

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(service.invoke, managed_context(), "prompt")
        assert entered.wait(timeout=5)
        request = service.get_request("account-1", "request-1")
        assert request.status is ManagedRequestStatus.RESERVED
        assert request.reserved_credits == 4
        assert ledger.balance_of("account-1") == 10
        release.set()
        result = future.result()

    assert result.status is ManagedRequestStatus.SUCCEEDED


def test_provider_success_atomically_charges_and_succeeds(tmp_path):
    database, ledger = funded_database(tmp_path)
    provider = StubProvider(output="safe completion")
    service = ManagedAccessService(database, provider, FlatPricingPolicy(4))

    result = service.invoke(managed_context(), "prompt")

    assert result == ManagedAccessResult(
        request_id="request-1",
        account_id="account-1",
        status=ManagedRequestStatus.SUCCEEDED,
        credits_charged=4,
        replayed=False,
        content="safe completion",
    )
    assert ledger.balance_of("account-1") == 6
    assert ledger.history_of("account-1")[-1].type is TransactionType.USAGE
    assert service.get_request("account-1", "request-1").status is ManagedRequestStatus.SUCCEEDED


def test_provider_failure_is_terminal_uncharged_and_releases_reservation(tmp_path):
    database, ledger = funded_database(tmp_path)
    provider = StubProvider(error=RuntimeError("provider unavailable"))
    service = ManagedAccessService(database, provider, FlatPricingPolicy(10))

    with pytest.raises(ManagedProviderError, match="managed provider request failed"):
        service.invoke(managed_context(), "prompt")

    assert ledger.balance_of("account-1") == 10
    assert len(ledger.history_of("account-1")) == 1
    assert service.get_request("account-1", "request-1").status is ManagedRequestStatus.FAILED

    replacement = StubProvider()
    replacement_service = ManagedAccessService(
        database, replacement, FlatPricingPolicy(10)
    )
    assert replacement_service.invoke(
        managed_context(request_id="request-2"), "prompt"
    ).status is ManagedRequestStatus.SUCCEEDED


def test_successful_replay_returns_metadata_without_calling_provider_again(tmp_path):
    database, ledger = funded_database(tmp_path)
    provider = StubProvider()
    service = ManagedAccessService(database, provider, FlatPricingPolicy(4))
    first = service.invoke(managed_context(), "prompt")

    replay = service.invoke(managed_context(), "prompt")

    assert first.replayed is False
    assert replay.replayed is True
    assert replay.content is None
    assert len(provider.calls) == 1
    assert ledger.balance_of("account-1") == 6
    assert len(ledger.history_of("account-1")) == 2


def test_failed_request_replay_is_terminal_and_never_calls_provider_again(tmp_path):
    database, _ledger = funded_database(tmp_path)
    provider = StubProvider(error=RuntimeError("failure"))
    service = ManagedAccessService(database, provider, FlatPricingPolicy(4))

    with pytest.raises(ManagedProviderError):
        service.invoke(managed_context(), "prompt")
    provider.error = None
    with pytest.raises(ManagedRequestFailedError, match="terminal"):
        service.invoke(managed_context(), "prompt")

    assert len(provider.calls) == 1


def test_same_request_id_with_different_payload_is_a_conflict(tmp_path):
    database, ledger = funded_database(tmp_path)
    provider = StubProvider()
    service = ManagedAccessService(database, provider, FlatPricingPolicy(4))
    service.invoke(managed_context(), "first prompt")

    with pytest.raises(ManagedRequestConflictError):
        service.invoke(managed_context(), "different prompt")

    assert len(provider.calls) == 1
    assert ledger.balance_of("account-1") == 6


def test_same_request_id_is_isolated_by_account(tmp_path):
    database, ledger = funded_database(
        tmp_path, accounts=("account-1", "account-2")
    )
    provider = StubProvider()
    service = ManagedAccessService(database, provider, FlatPricingPolicy(4))

    first = service.invoke(managed_context("account-1", "shared"), "prompt")
    second = service.invoke(managed_context("account-2", "shared"), "prompt")

    assert first.account_id == "account-1"
    assert second.account_id == "account-2"
    assert len(provider.calls) == 2
    assert ledger.balance_of("account-1") == 6
    assert ledger.balance_of("account-2") == 6


def test_concurrent_same_request_calls_provider_once(tmp_path):
    database, _ledger = funded_database(tmp_path)
    entered = Event()
    release = Event()
    provider = StubProvider(entered=entered, release=release)
    service = ManagedAccessService(database, provider, FlatPricingPolicy(4))

    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(service.invoke, managed_context(), "prompt")
        assert entered.wait(timeout=5)
        second = executor.submit(service.invoke, managed_context(), "prompt")
        with pytest.raises(ManagedRequestRecoveryRequiredError):
            second.result(timeout=5)
        release.set()
        assert first.result(timeout=5).status is ManagedRequestStatus.SUCCEEDED

    assert len(provider.calls) == 1


def test_active_reservation_prevents_concurrent_overspend(tmp_path):
    database, ledger = funded_database(tmp_path, amount=10)
    entered = Event()
    release = Event()
    provider = StubProvider(entered=entered, release=release)
    service = ManagedAccessService(database, provider, FlatPricingPolicy(8))

    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(
            service.invoke, managed_context(request_id="request-1"), "first"
        )
        assert entered.wait(timeout=5)
        with pytest.raises(InsufficientCreditsError):
            service.invoke(managed_context(request_id="request-2"), "second")
        release.set()
        first.result(timeout=5)

    assert len(provider.calls) == 1
    assert ledger.balance_of("account-1") == 2


def test_concurrent_different_requests_same_account_allow_at_most_one_overspend(tmp_path):
    database, ledger = funded_database(tmp_path, amount=10)
    provider = StubProvider()
    service = ManagedAccessService(database, provider, FlatPricingPolicy(8))

    def invoke(request_id):
        try:
            return service.invoke(managed_context(request_id=request_id), request_id)
        except InsufficientCreditsError as error:
            return error

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(invoke, ("one", "two")))

    assert sum(isinstance(item, ManagedAccessResult) for item in outcomes) == 1
    assert sum(isinstance(item, InsufficientCreditsError) for item in outcomes) == 1
    assert len(provider.calls) == 1
    assert ledger.balance_of("account-1") == 2


@pytest.mark.parametrize(
    "failure_point",
    [
        "before_usage_append",
        "after_usage_append_before_idempotency_commit",
        "before_request_final_status_commit",
    ],
)
def test_provider_success_plus_finalize_failure_is_recoverable_without_partial_charge(
    tmp_path, failure_point
):
    database, ledger = funded_database(tmp_path)
    provider = StubProvider()
    service = ManagedAccessService(
        database,
        provider,
        FlatPricingPolicy(4),
        fault_injector=FailOnce(failure_point),
    )

    with pytest.raises(ManagedFinalizationError, match="requires reconciliation"):
        service.invoke(managed_context(), "prompt")

    request = service.get_request("account-1", "request-1")
    assert request.status is ManagedRequestStatus.FINALIZATION_FAILED
    assert request.reserved_credits == 4
    assert ledger.balance_of("account-1") == 10
    assert len(ledger.history_of("account-1")) == 1
    with sqlite3.connect(database) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM credit_idempotency"
        ).fetchone()[0] == 0

    with pytest.raises(ManagedFinalizationError, match="already succeeded"):
        service.invoke(managed_context(), "prompt")
    assert len(provider.calls) == 1


def test_finalization_failed_reservation_remains_unavailable(tmp_path):
    database, _ledger = funded_database(tmp_path, amount=4)
    provider = StubProvider()
    service = ManagedAccessService(
        database,
        provider,
        FlatPricingPolicy(4),
        fault_injector=FailOnce("before_usage_append"),
    )
    with pytest.raises(ManagedFinalizationError):
        service.invoke(managed_context(), "prompt")

    with pytest.raises(InsufficientCreditsError):
        service.invoke(managed_context(request_id="request-2"), "prompt")

    assert len(provider.calls) == 1


def test_failure_before_reservation_commit_rolls_back_without_provider_call(tmp_path):
    database, ledger = funded_database(tmp_path)
    provider = StubProvider()
    service = ManagedAccessService(
        database,
        provider,
        FlatPricingPolicy(4),
        fault_injector=FailOnce("before_reservation_commit"),
    )

    with pytest.raises(ManagedAccessError, match="could not be reserved"):
        service.invoke(managed_context(), "prompt")

    assert service.get_request("account-1", "request-1") is None
    assert provider.calls == []
    assert ledger.balance_of("account-1") == 10


def test_failure_after_reservation_commit_keeps_visible_non_retriable_state(tmp_path):
    database, ledger = funded_database(tmp_path)
    provider = StubProvider()
    service = ManagedAccessService(
        database,
        provider,
        FlatPricingPolicy(4),
        fault_injector=FailOnce("after_reservation_commit"),
    )

    with pytest.raises(ManagedRequestRecoveryRequiredError, match="reserved"):
        service.invoke(managed_context(), "prompt")

    assert service.get_request("account-1", "request-1").status is ManagedRequestStatus.RESERVED
    assert provider.calls == []
    assert ledger.balance_of("account-1") == 10
    with pytest.raises(ManagedRequestRecoveryRequiredError):
        service.invoke(managed_context(), "prompt")
    assert provider.calls == []


def test_succeeded_request_replays_after_service_restart(tmp_path):
    database, ledger = funded_database(tmp_path)
    first_provider = StubProvider()
    first = ManagedAccessService(database, first_provider, FlatPricingPolicy(4))
    first.invoke(managed_context(), "prompt")
    first.close()

    second_provider = StubProvider()
    second = ManagedAccessService(database, second_provider, FlatPricingPolicy(4))
    replay = second.invoke(managed_context(), "prompt")

    assert replay.replayed is True
    assert replay.content is None
    assert second_provider.calls == []
    assert ledger.balance_of("account-1") == 6


def test_secret_never_enters_result_repr_exception_or_sqlite(tmp_path):
    secret = "sk-platform-super-secret"
    database, _ledger = funded_database(tmp_path)

    class SecretHoldingProvider(StubProvider):
        def __init__(self, fail=False):
            super().__init__()
            self.credential = RuntimeCredential(secret)
            self.fail = fail

        def invoke(self, *, model_config, prompt):
            self.calls.append((model_config, prompt))
            if self.fail:
                raise RuntimeError(f"provider rejected {secret}")
            return "safe completion"

    provider = SecretHoldingProvider()
    service = ManagedAccessService(database, provider, FlatPricingPolicy(4))
    context = managed_context()
    result = service.invoke(context, "prompt")
    request = service.get_request("account-1", "request-1")

    assert secret not in repr(service)
    assert secret not in repr(context)
    assert secret not in repr(request)
    assert secret not in repr(result)
    assert secret.encode() not in database.read_bytes()

    failing_database = tmp_path / "failing.sqlite3"
    failing_ledger = SQLiteCreditLedger(failing_database)
    failing_ledger.grant("account-1", 10)
    failing = ManagedAccessService(
        failing_database, SecretHoldingProvider(fail=True), FlatPricingPolicy(4)
    )
    with pytest.raises(ManagedProviderError) as captured:
        failing.invoke(managed_context(), "prompt")
    assert secret not in str(captured.value)
    assert secret not in repr(captured.value)
    assert captured.value.__context__ is None
    assert secret.encode() not in failing_database.read_bytes()


def test_structural_security_guard_keeps_public_surface_unprivileged(tmp_path):
    database, _ledger = funded_database(tmp_path)
    service = ManagedAccessService(database, StubProvider(), FlatPricingPolicy(4))
    public_names = {name for name in dir(service) if not name.startswith("_")}

    assert {"grant", "refund", "adjust", "ledger"}.isdisjoint(public_names)
    assert public_names == {"close", "get_request", "invoke"}

    for domain_type in (LLMAccessContext, ManagedRequest, ManagedAccessResult):
        names = {item.name.lower() for item in fields(domain_type)}
        assert "credential" not in names
        assert "api_key" not in names
        assert "client" not in names
        assert "provider" not in names


def test_managed_schema_contains_no_credential_or_response_payload(tmp_path):
    database, _ledger = funded_database(tmp_path)
    service = ManagedAccessService(database, StubProvider(), FlatPricingPolicy(4))
    service.invoke(managed_context(), "prompt")

    with sqlite3.connect(database) as connection:
        columns = {
            row[1]
            for table in ("managed_requests", "credit_transactions", "credit_idempotency")
            for row in connection.execute(f"PRAGMA table_info({table})")
        }

    forbidden = {"credential", "api_key", "client", "provider_object", "response"}
    assert columns.isdisjoint(forbidden)
