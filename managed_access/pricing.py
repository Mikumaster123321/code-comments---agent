from __future__ import annotations

import hashlib
import json
from decimal import MAX_EMAX, MIN_EMIN, ROUND_CEILING, Decimal, localcontext
from typing import Protocol, runtime_checkable

from llm_provider import ModelConfig

from .domain import (
    InvalidPricingContextError,
    InvalidUsageError,
    PricingContext,
    UsageRecord,
)


class InvalidFlatPricingError(ValueError):
    """Raised when the flat request price is not a positive integer."""


class InvalidTokenPricingError(ValueError):
    """Raised when token rates cannot define deterministic Decimal pricing."""


@runtime_checkable
class PricingPolicy(Protocol):
    @property
    def policy_id(self) -> str: ...

    def reserve_credits(self, context: PricingContext) -> int: ...

    def price_usage(
        self, context: PricingContext, usage: UsageRecord | None
    ) -> int: ...


class FlatPricingPolicy:
    def __init__(self, credits_per_request: int) -> None:
        if (
            not isinstance(credits_per_request, int)
            or isinstance(credits_per_request, bool)
            or credits_per_request <= 0
        ):
            raise InvalidFlatPricingError(
                "credits_per_request must be a positive integer"
            )
        self._credits_per_request = credits_per_request

    @property
    def policy_id(self) -> str:
        return f"flat:v1:{self._credits_per_request}"

    def reserve_credits(self, context: PricingContext) -> int:
        if not isinstance(context, PricingContext):
            raise TypeError("context must be a PricingContext")
        return self._credits_per_request

    def price_usage(
        self, context: PricingContext, usage: UsageRecord | None
    ) -> int:
        return self.reserve_credits(context)

    def credits_for(self, model_config: ModelConfig) -> int:
        if not isinstance(model_config, ModelConfig):
            raise TypeError("model_config must be a ModelConfig")
        return self._credits_per_request


class TokenPricingPolicy:
    """Prices synthetic Credit rates per 1,000 tokens using Decimal only."""

    TOKENS_PER_RATE_UNIT = 1000

    def __init__(
        self,
        input_credits_per_1000_tokens: Decimal,
        output_credits_per_1000_tokens: Decimal,
    ) -> None:
        self._input_rate = self._validate_rate(
            input_credits_per_1000_tokens, "input_credits_per_1000_tokens"
        )
        self._output_rate = self._validate_rate(
            output_credits_per_1000_tokens, "output_credits_per_1000_tokens"
        )
        if self._input_rate == 0 and self._output_rate == 0:
            raise InvalidTokenPricingError("at least one token rate must be positive")
        identity = json.dumps(
            {
                "input": self._canonical_decimal(self._input_rate),
                "output": self._canonical_decimal(self._output_rate),
                "unit": self.TOKENS_PER_RATE_UNIT,
                "version": 1,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("ascii")
        self._policy_id = f"token:v1:{hashlib.sha256(identity).hexdigest()}"

    @property
    def policy_id(self) -> str:
        return self._policy_id

    def reserve_credits(self, context: PricingContext) -> int:
        if not isinstance(context, PricingContext):
            raise TypeError("context must be a PricingContext")
        reserved = self._price(context.max_input_tokens, context.max_output_tokens)
        if reserved <= 0:
            raise InvalidPricingContextError(
                "token pricing limits must produce a positive reservation"
            )
        return reserved

    def price_usage(
        self, context: PricingContext, usage: UsageRecord | None
    ) -> int:
        if not isinstance(context, PricingContext):
            raise TypeError("context must be a PricingContext")
        if not isinstance(usage, UsageRecord):
            raise InvalidUsageError("token pricing requires a valid UsageRecord")
        try:
            validated = UsageRecord(
                provider_id=usage.provider_id,
                model=usage.model,
                input_tokens=usage.input_tokens,
                output_tokens=usage.output_tokens,
            )
        except Exception:
            raise InvalidUsageError("token pricing requires a valid UsageRecord") from None
        if (
            validated.provider_id != context.provider_id
            or validated.model != context.model
        ):
            raise InvalidUsageError(
                "usage provider and model must match the pricing context"
            )
        if (
            validated.input_tokens > context.max_input_tokens
            or validated.output_tokens > context.max_output_tokens
        ):
            raise InvalidUsageError("usage exceeds the declared token limits")
        return self._price(validated.input_tokens, validated.output_tokens)

    def _price(self, input_tokens: int, output_tokens: int) -> int:
        terms = tuple(
            (rate, tokens)
            for rate, tokens in (
                (self._input_rate, input_tokens),
                (self._output_rate, output_tokens),
            )
            if rate != 0 and tokens != 0
        )
        if not terms:
            return 0

        minimum_exponent = min(rate.as_tuple().exponent for rate, _ in terms)
        precision = max(
            len(rate.as_tuple().digits)
            + self._integer_decimal_digits(tokens)
            + rate.as_tuple().exponent
            - minimum_exponent
            for rate, tokens in terms
        ) + 2
        with localcontext() as context:
            context.prec = precision
            context.rounding = ROUND_CEILING
            context.Emax = MAX_EMAX
            context.Emin = MIN_EMIN
            context.clamp = 0
            amount = sum(
                rate * Decimal(tokens) for rate, tokens in terms
            ) / Decimal(self.TOKENS_PER_RATE_UNIT)
            return int(amount.to_integral_value(rounding=ROUND_CEILING))

    @staticmethod
    def _validate_rate(value: Decimal, field_name: str) -> Decimal:
        if not isinstance(value, Decimal) or isinstance(value, bool):
            raise InvalidTokenPricingError(f"{field_name} must be a Decimal")
        if not value.is_finite() or value < 0:
            raise InvalidTokenPricingError(
                f"{field_name} must be finite and non-negative"
            )
        return value

    @staticmethod
    def _canonical_decimal(value: Decimal) -> str:
        if value == 0:
            return "0"
        decimal_tuple = value.as_tuple()
        digits = list(decimal_tuple.digits)
        exponent = decimal_tuple.exponent
        while digits[-1] == 0:
            digits.pop()
            exponent += 1
        text = "".join(str(digit) for digit in digits)
        point = len(text) + exponent
        if point <= 0:
            return f"0.{('0' * -point)}{text}"
        if point < len(text):
            return f"{text[:point]}.{text[point:]}"
        return f"{text}{'0' * (point - len(text))}"

    @staticmethod
    def _integer_decimal_digits(value: int) -> int:
        estimate = (value.bit_length() * 30103) // 100000 + 1
        if value < 10 ** (estimate - 1):
            return estimate - 1
        return estimate
