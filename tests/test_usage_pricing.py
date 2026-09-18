from dataclasses import FrozenInstanceError, fields
from decimal import (
    ROUND_CEILING,
    ROUND_DOWN,
    ROUND_FLOOR,
    ROUND_HALF_EVEN,
    ROUND_UP,
    Decimal,
    getcontext,
    localcontext,
)
from fractions import Fraction

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


def _decimal_fraction(value):
    decimal_tuple = value.as_tuple()
    coefficient = int("".join(str(digit) for digit in decimal_tuple.digits))
    if decimal_tuple.exponent >= 0:
        return Fraction(coefficient * 10**decimal_tuple.exponent, 1)
    return Fraction(coefficient, 10 ** -decimal_tuple.exponent)


def _exact_credits(input_rate, output_rate, input_tokens, output_tokens):
    amount = (
        _decimal_fraction(input_rate) * input_tokens
        + _decimal_fraction(output_rate) * output_tokens
    ) / 1000
    return -(-amount.numerator // amount.denominator)


def test_token_pricing_is_independent_of_ambient_decimal_context():
    input_rate = Decimal("1.0000001")
    output_rate = Decimal("1.9999999")
    policy = TokenPricingPolicy(input_rate, output_rate)
    pricing_context = PricingContext("openai", "test-model", 1000, 1000)
    record = UsageRecord("openai", "test-model", 1000, 0)
    expected_reservation = policy.reserve_credits(pricing_context)
    expected_usage = policy.price_usage(pricing_context, record)
    original = getcontext().copy()

    for precision in (1, 2, 5, 7, 8, 16, 28, 50):
        for rounding in (
            ROUND_DOWN,
            ROUND_UP,
            ROUND_HALF_EVEN,
            ROUND_FLOOR,
            ROUND_CEILING,
        ):
            with localcontext() as ambient:
                ambient.prec = precision
                ambient.rounding = rounding
                assert policy.reserve_credits(pricing_context) == expected_reservation
                assert policy.price_usage(pricing_context, record) == expected_usage
                assert (
                    TokenPricingPolicy(input_rate, output_rate).policy_id
                    == policy.policy_id
                )

    current = getcontext()
    assert current.prec == original.prec
    assert current.rounding == original.rounding
    assert current.Emin == original.Emin
    assert current.Emax == original.Emax
    assert current.traps == original.traps


@pytest.mark.parametrize(
    ("rate", "expected"),
    [
        (Decimal("1.0"), 1),
        (Decimal("1.0000001"), 2),
        (Decimal("1.9999999"), 2),
        (Decimal("2.0"), 2),
        (Decimal("0.0000000000000000000000000001"), 1),
    ],
)
def test_round_ceiling_boundaries_remain_unchanged(rate, expected):
    policy = TokenPricingPolicy(rate, Decimal("0"))
    pricing_context = PricingContext("openai", "test-model", 1000, 0)

    assert policy.reserve_credits(pricing_context) == expected
    assert policy.price_usage(
        pricing_context, UsageRecord("openai", "test-model", 1000, 0)
    ) == expected


def test_large_decimal_rates_and_tokens_price_exactly_beyond_precision_28():
    input_rate = Decimal(
        "123456789012345678901234567890.12345678901234567890123456789"
    )
    output_rate = Decimal(
        "0.0000000000000000000000000000000000000001234567890123456789"
    )
    max_input_tokens = 10**40 + 12345678901234567890
    max_output_tokens = 10**36 + 987654321
    actual_input_tokens = 10**35 + 24680
    actual_output_tokens = 10**33 + 13579
    policy = TokenPricingPolicy(input_rate, output_rate)
    pricing_context = PricingContext(
        "openai", "test-model", max_input_tokens, max_output_tokens
    )
    record = UsageRecord(
        "openai", "test-model", actual_input_tokens, actual_output_tokens
    )

    with localcontext() as ambient:
        ambient.prec = 1
        ambient.rounding = ROUND_DOWN
        assert policy.reserve_credits(pricing_context) == _exact_credits(
            input_rate,
            output_rate,
            max_input_tokens,
            max_output_tokens,
        )
        assert policy.price_usage(pricing_context, record) == _exact_credits(
            input_rate,
            output_rate,
            actual_input_tokens,
            actual_output_tokens,
        )


def test_arbitrary_size_integer_tokens_do_not_require_string_conversion():
    tokens = 10**4500
    policy = TokenPricingPolicy(Decimal("1"), Decimal("0"))
    pricing_context = PricingContext("openai", "test-model", tokens, 0)

    assert policy.reserve_credits(pricing_context) == 10**4497
