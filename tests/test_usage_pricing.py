from dataclasses import FrozenInstanceError, fields
from decimal import Decimal

import pytest

from managed_access import (
    FlatPricingPolicy,
    InvalidPricingContextError,
    InvalidTokenPricingError,
    InvalidUsageError,
    PricingContext,
    PricingPolicy,
    TokenPricingPolicy,
    UsageRecord,
)


CONTEXT = PricingContext("openai", "test-model", 2000, 3000)


def usage(input_tokens=1000, output_tokens=500, provider_id="openai", model="test-model"):
    return UsageRecord(provider_id, model, input_tokens, output_tokens)


def test_usage_record_is_immutable_normalized_and_has_total_tokens():
    record = UsageRecord(" OpenAI ", " test-model ", 10, 4)

    assert record.provider_id == "openai"
    assert record.model == "test-model"
    assert record.total_tokens == 14
    with pytest.raises(FrozenInstanceError):
        record.input_tokens = 20


@pytest.mark.parametrize(("input_tokens", "output_tokens"), [(0, 1), (1, 0)])
def test_usage_record_accepts_one_sided_usage(input_tokens, output_tokens):
    assert usage(input_tokens, output_tokens).total_tokens == 1


@pytest.mark.parametrize(
    ("input_tokens", "output_tokens"),
    [(-1, 1), (1, -1), (True, 1), (1, False), (0, 0)],
)
def test_usage_record_rejects_invalid_or_empty_token_counts(
    input_tokens, output_tokens
):
    with pytest.raises(InvalidUsageError):
        usage(input_tokens, output_tokens)


@pytest.mark.parametrize(("provider_id", "model"), [("", "m"), ("p", " "), (1, "m")])
def test_usage_record_requires_provider_and_model(provider_id, model):
    with pytest.raises(InvalidUsageError):
        usage(provider_id=provider_id, model=model)


def test_usage_record_structure_is_credential_and_payload_free():
    names = {item.name for item in fields(UsageRecord)}

    assert names == {"provider_id", "model", "input_tokens", "output_tokens"}
    assert names.isdisjoint(
        {"credential", "api_key", "prompt", "completion", "request", "response", "client"}
    )


@pytest.mark.parametrize(
    "value",
    [1.0, True, 1, "1", Decimal("NaN"), Decimal("Infinity"), Decimal("-0.1")],
)
def test_token_pricing_rejects_non_decimal_or_invalid_rates(value):
    with pytest.raises(InvalidTokenPricingError):
        TokenPricingPolicy(value, Decimal("1"))


def test_token_pricing_rejects_two_zero_rates():
    with pytest.raises(InvalidTokenPricingError):
        TokenPricingPolicy(Decimal("0"), Decimal("0.00"))


@pytest.mark.parametrize(
    ("policy", "record", "expected"),
    [
        (TokenPricingPolicy(Decimal("2"), Decimal("0")), usage(1000, 0), 2),
        (TokenPricingPolicy(Decimal("2.01"), Decimal("0")), usage(1000, 0), 3),
        (TokenPricingPolicy(Decimal("0.0001"), Decimal("0")), usage(1, 0), 1),
        (TokenPricingPolicy(Decimal("1"), Decimal("0")), usage(500, 0), 1),
        (TokenPricingPolicy(Decimal("0"), Decimal("2")), usage(0, 500), 1),
        (TokenPricingPolicy(Decimal("1"), Decimal("2")), usage(1000, 500), 2),
    ],
)
def test_token_pricing_uses_decimal_and_round_ceiling(policy, record, expected):
    assert policy.price_usage(CONTEXT, record) == expected
    assert policy.price_usage(CONTEXT, record) == expected


def test_token_reservation_prices_declared_upper_bound():
    policy = TokenPricingPolicy(Decimal("1.25"), Decimal("2.5"))

    assert policy.reserve_credits(CONTEXT) == 10


def test_token_reservation_requires_a_positive_priced_upper_bound():
    policy = TokenPricingPolicy(Decimal("1"), Decimal("0"))

    with pytest.raises(InvalidPricingContextError):
        policy.reserve_credits(PricingContext("openai", "test-model", 0, 100))


def test_token_pricing_requires_usage_and_matching_identity_and_limits():
    policy = TokenPricingPolicy(Decimal("1"), Decimal("1"))

    with pytest.raises(InvalidUsageError):
        policy.price_usage(CONTEXT, None)
    with pytest.raises(InvalidUsageError):
        policy.price_usage(CONTEXT, usage(provider_id="other"))
    with pytest.raises(InvalidUsageError):
        policy.price_usage(CONTEXT, usage(model="other"))
    with pytest.raises(InvalidUsageError):
        policy.price_usage(CONTEXT, usage(input_tokens=2001, output_tokens=0))


def test_policy_identity_is_stable_and_configuration_sensitive():
    first = TokenPricingPolicy(Decimal("1.0"), Decimal("2.00"))
    equivalent = TokenPricingPolicy(Decimal("1"), Decimal("2"))
    different = TokenPricingPolicy(Decimal("1"), Decimal("3"))

    assert first.policy_id == equivalent.policy_id
    assert first.policy_id != different.policy_id
    assert first.policy_id.startswith("token:v1:")
    assert FlatPricingPolicy(4).policy_id == FlatPricingPolicy(4).policy_id
    assert FlatPricingPolicy(4).policy_id != FlatPricingPolicy(5).policy_id
    assert isinstance(first, PricingPolicy)


def test_flat_pricing_implements_quote_and_actual_contract_without_usage():
    policy = FlatPricingPolicy(4)

    assert policy.reserve_credits(CONTEXT) == 4
    assert policy.price_usage(CONTEXT, None) == 4
