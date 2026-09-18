import ast
from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from pathlib import Path
from threading import Barrier

import pytest

from credits import (
    CreditAccount,
    CreditTransaction,
    IdempotencyConflictError,
    InMemoryCreditLedger,
    InsufficientCreditsError,
    InvalidAccountError,
    InvalidCreditAmountError,
    InvalidRequestIdError,
    TransactionType,
)


def make_transaction(
    transaction_type: TransactionType,
    amount: int,
    request_id: str | None = None,
) -> CreditTransaction:
    return CreditTransaction(
        transaction_id="transaction-1",
        account_id="account-1",
        type=transaction_type,
        amount=amount,
        request_id=request_id,
        created_at=datetime.now(timezone.utc),
        note="test",
    )


def test_credit_account_is_immutable_and_normalizes_its_identifier():
    account = CreditAccount("  account-1  ")

    assert account.account_id == "account-1"
    with pytest.raises(FrozenInstanceError):
        account.account_id = "other"


@pytest.mark.parametrize("account_id", ["", "   ", None, 1])
def test_credit_account_rejects_invalid_identifiers(account_id):
    with pytest.raises(InvalidAccountError):
        CreditAccount(account_id)


def test_credit_transaction_is_immutable():
    transaction = make_transaction(TransactionType.ADMIN_GRANT, 10)

    with pytest.raises(FrozenInstanceError):
        transaction.amount = 20


@pytest.mark.parametrize(
    ("transaction_type", "amount", "request_id"),
    [
        (TransactionType.ADMIN_GRANT, 0, None),
        (TransactionType.ADMIN_GRANT, -1, None),
        (TransactionType.USAGE, 1, "usage-1"),
        (TransactionType.USAGE, 0, "usage-1"),
        (TransactionType.REFUND, -1, "refund-1"),
        (TransactionType.REFUND, 0, "refund-1"),
        (TransactionType.ADJUSTMENT, 0, None),
    ],
)
def test_credit_transaction_enforces_amount_signs(
    transaction_type, amount, request_id
):
    with pytest.raises(InvalidCreditAmountError):
        make_transaction(transaction_type, amount, request_id)


@pytest.mark.parametrize("amount", [True, False, 1.0, "1"])
def test_credit_transaction_requires_integer_amount_and_rejects_bool(amount):
    with pytest.raises(InvalidCreditAmountError):
        make_transaction(TransactionType.ADMIN_GRANT, amount)


def test_transaction_types_are_exactly_the_phase_one_types():
    assert {transaction_type.name for transaction_type in TransactionType} == {
        "ADMIN_GRANT",
        "USAGE",
        "REFUND",
        "ADJUSTMENT",
    }


def test_grant_appends_an_admin_grant_and_updates_derived_balance():
    ledger = InMemoryCreditLedger()

    transaction = ledger.grant("account-1", 10, "initial grant")

    assert transaction.type is TransactionType.ADMIN_GRANT
    assert transaction.amount == 10
    assert transaction.request_id is None
    assert ledger.balance_of("account-1") == 10
    assert ledger.history_of("account-1") == (transaction,)


@pytest.mark.parametrize("amount", [0, -1, True, 1.5])
def test_grant_rejects_non_positive_or_non_integer_amount_without_state_change(amount):
    ledger = InMemoryCreditLedger()

    with pytest.raises(InvalidCreditAmountError):
        ledger.grant("account-1", amount)

    assert ledger.balance_of("account-1") == 0
    assert ledger.history_of("account-1") == ()


def test_balance_is_the_sum_of_append_only_transaction_amounts():
    ledger = InMemoryCreditLedger()
    ledger.grant("account-1", 20)
    ledger.charge("account-1", "usage-1", 7)
    ledger.refund("account-1", "refund-1", 2)
    ledger.adjust("account-1", -3)

    history = ledger.history_of("account-1")
    assert ledger.balance_of("account-1") == sum(item.amount for item in history) == 12


def test_charge_accepts_positive_amount_and_records_negative_usage():
    ledger = InMemoryCreditLedger()
    ledger.grant("account-1", 10)

    transaction = ledger.charge("account-1", "usage-1", 4, "analysis")

    assert transaction.type is TransactionType.USAGE
    assert transaction.amount == -4
    assert transaction.request_id == "usage-1"
    assert ledger.balance_of("account-1") == 6


def test_charge_may_consume_the_exact_balance():
    ledger = InMemoryCreditLedger()
    ledger.grant("account-1", 10)

    ledger.charge("account-1", "usage-1", 10)

    assert ledger.balance_of("account-1") == 0


def test_insufficient_charge_has_no_state_change():
    ledger = InMemoryCreditLedger()
    grant = ledger.grant("account-1", 10)

    with pytest.raises(InsufficientCreditsError):
        ledger.charge("account-1", "usage-1", 11)

    assert ledger.balance_of("account-1") == 10
    assert ledger.history_of("account-1") == (grant,)

    retry = ledger.charge("account-1", "usage-1", 4)
    assert retry.amount == -4
    assert ledger.balance_of("account-1") == 6


@pytest.mark.parametrize("amount", [0, -1, True, 1.5])
def test_charge_rejects_non_positive_or_non_integer_amount(amount):
    ledger = InMemoryCreditLedger()
    ledger.grant("account-1", 10)
    before = ledger.history_of("account-1")

    with pytest.raises(InvalidCreditAmountError):
        ledger.charge("account-1", "usage-1", amount)

    assert ledger.history_of("account-1") == before
    assert ledger.balance_of("account-1") == 10


@pytest.mark.parametrize("request_id", ["", "   ", None, 1])
def test_charge_requires_a_non_empty_request_id(request_id):
    ledger = InMemoryCreditLedger()
    ledger.grant("account-1", 10)

    with pytest.raises(InvalidRequestIdError):
        ledger.charge("account-1", request_id, 1)

    assert ledger.balance_of("account-1") == 10


def test_charge_retry_returns_the_original_transaction_without_double_charge():
    ledger = InMemoryCreditLedger()
    ledger.grant("account-1", 10)

    first = ledger.charge("account-1", "usage-1", 4, "analysis")
    retry = ledger.charge("account-1", "usage-1", 4, "analysis")

    assert retry is first
    assert ledger.balance_of("account-1") == 6
    assert len(ledger.history_of("account-1")) == 2


def test_charge_idempotency_conflict_has_no_state_or_index_change():
    ledger = InMemoryCreditLedger()
    ledger.grant("account-1", 10)
    original = ledger.charge("account-1", "usage-1", 4, "analysis")
    before = ledger.history_of("account-1")

    with pytest.raises(IdempotencyConflictError):
        ledger.charge("account-1", "usage-1", 5, "analysis")

    assert ledger.history_of("account-1") == before
    assert ledger.balance_of("account-1") == 6
    assert ledger.charge("account-1", "usage-1", 4, "analysis") is original


def test_same_charge_request_id_is_isolated_by_account():
    ledger = InMemoryCreditLedger()
    ledger.grant("account-1", 10)
    ledger.grant("account-2", 10)

    first = ledger.charge("account-1", "shared-request", 3)
    second = ledger.charge("account-2", "shared-request", 4)

    assert first is not second
    assert ledger.balance_of("account-1") == 7
    assert ledger.balance_of("account-2") == 6


def test_refund_is_positive_and_idempotent():
    ledger = InMemoryCreditLedger()

    first = ledger.refund("account-1", "refund-1", 5, "service recovery")
    retry = ledger.refund("account-1", "refund-1", 5, "service recovery")

    assert first.type is TransactionType.REFUND
    assert first.amount == 5
    assert retry is first
    assert ledger.balance_of("account-1") == 5
    assert ledger.history_of("account-1") == (first,)


def test_refund_idempotency_conflict_has_no_state_change():
    ledger = InMemoryCreditLedger()
    original = ledger.refund("account-1", "refund-1", 5)

    with pytest.raises(IdempotencyConflictError):
        ledger.refund("account-1", "refund-1", 6)

    assert ledger.history_of("account-1") == (original,)
    assert ledger.balance_of("account-1") == 5


@pytest.mark.parametrize(
    ("request_id", "amount", "expected_error"),
    [
        ("refund-1", 0, InvalidCreditAmountError),
        ("refund-1", -1, InvalidCreditAmountError),
        ("", 1, InvalidRequestIdError),
    ],
)
def test_invalid_refund_has_no_state_change(request_id, amount, expected_error):
    ledger = InMemoryCreditLedger()

    with pytest.raises(expected_error):
        ledger.refund("account-1", request_id, amount)

    assert ledger.balance_of("account-1") == 0
    assert ledger.history_of("account-1") == ()

    if request_id == "refund-1":
        retry = ledger.refund("account-1", request_id, 1)
        assert retry.amount == 1
        assert ledger.history_of("account-1") == (retry,)


def test_adjust_supports_positive_and_safe_negative_amounts():
    ledger = InMemoryCreditLedger()

    positive = ledger.adjust("account-1", 10, "correction")
    negative = ledger.adjust("account-1", -4, "correction")

    assert positive.type is TransactionType.ADJUSTMENT
    assert negative.type is TransactionType.ADJUSTMENT
    assert ledger.balance_of("account-1") == 6


def test_adjust_rejects_zero_and_negative_balance_without_state_change():
    ledger = InMemoryCreditLedger()
    original = ledger.adjust("account-1", 5)

    with pytest.raises(InvalidCreditAmountError):
        ledger.adjust("account-1", 0)
    with pytest.raises(InsufficientCreditsError):
        ledger.adjust("account-1", -6)

    assert ledger.history_of("account-1") == (original,)
    assert ledger.balance_of("account-1") == 5


def test_accounts_are_isolated_and_unknown_valid_account_has_zero_balance():
    ledger = InMemoryCreditLedger()
    ledger.grant("account-1", 10)
    ledger.grant("account-2", 20)
    ledger.charge("account-1", "usage-1", 3)

    assert ledger.balance_of("account-1") == 7
    assert ledger.balance_of("account-2") == 20
    assert ledger.balance_of("account-3") == 0
    assert all(
        transaction.account_id == "account-1"
        for transaction in ledger.history_of("account-1")
    )


def test_history_uses_append_order_and_returns_an_immutable_tuple():
    ledger = InMemoryCreditLedger()
    grant = ledger.grant("account-1", 10)
    charge = ledger.charge("account-1", "usage-1", 2)
    refund = ledger.refund("account-1", "refund-1", 1)

    history = ledger.history_of("account-1")

    assert history == (grant, charge, refund)
    assert isinstance(history, tuple)
    with pytest.raises(AttributeError):
        history.append(grant)


def test_transaction_ids_are_unique():
    ledger = InMemoryCreditLedger()

    transactions = [ledger.grant("account-1", 1) for _ in range(100)]

    assert len({transaction.transaction_id for transaction in transactions}) == 100


def test_concurrent_same_account_charges_cannot_overdraw():
    ledger = InMemoryCreditLedger()
    ledger.grant("account-1", 10)
    barrier = Barrier(3)

    def charge(request_id):
        barrier.wait()
        try:
            return ledger.charge("account-1", request_id, 8)
        except InsufficientCreditsError as error:
            return error

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(charge, request_id) for request_id in ("one", "two")]
        barrier.wait()
        outcomes = [future.result() for future in futures]

    assert sum(isinstance(outcome, CreditTransaction) for outcome in outcomes) == 1
    assert sum(isinstance(outcome, InsufficientCreditsError) for outcome in outcomes) == 1
    assert ledger.balance_of("account-1") == 2
    assert [
        item.type for item in ledger.history_of("account-1")
    ].count(TransactionType.USAGE) == 1


def test_credits_package_has_no_forbidden_imports():
    forbidden_roots = {
        "llm_provider",
        "llm_service",
        "config",
        "processor",
        "ui",
        "openai",
        "gradio",
        "code_maintenance",
        "sqlite3",
        "requests",
        "http",
        "socket",
    }
    credits_directory = Path(__file__).resolve().parents[1] / "credits"

    imported_roots = set()
    for source_path in credits_directory.glob("*.py"):
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                imported_roots.add(node.module.split(".", 1)[0])

    assert imported_roots.isdisjoint(forbidden_roots)
