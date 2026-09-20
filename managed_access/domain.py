from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from credits import InvalidCreditAmountError
from credits.domain import (
    normalize_account_id,
    normalize_request_id,
    validate_integer_amount,
)
from llm_provider import ModelConfig


class ManagedAccessError(Exception):
    """Base class for safe Managed Access failures."""


class InvalidAccessContextError(ManagedAccessError):
    """Raised when an access context violates its mode contract."""


class InvalidUsageError(ManagedAccessError):
    """Raised when metered usage is missing, malformed, or inconsistent."""


class InvalidPricingContextError(ManagedAccessError):
    """Raised when a pricing context cannot define a safe reservation."""


class ManagedRequestConflictError(ManagedAccessError):
    """Raised when a request ID is reused with a different payload."""


class ManagedProviderError(ManagedAccessError):
    """Raised when the server-side Provider fails."""


class ManagedFinalizationError(ManagedAccessError):
    """Raised when Provider success cannot be atomically accounted for."""


class ManagedRequestRecoveryRequiredError(ManagedAccessError):
    """Raised when a non-terminal request must not be invoked again."""


class ManagedRequestFailedError(ManagedAccessError):
    """Raised when replaying a terminal Provider-failed request."""


class LLMAccessMode(str, Enum):
    BYOK = "BYOK"
    MANAGED = "MANAGED"


class ManagedRequestStatus(str, Enum):
    RESERVED = "RESERVED"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    FINALIZATION_FAILED = "FINALIZATION_FAILED"


@dataclass(frozen=True)
class LLMAccessContext:
    mode: LLMAccessMode
    model_config: ModelConfig
    account_id: str | None = None
    request_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.mode, LLMAccessMode):
            raise InvalidAccessContextError("mode must be an LLMAccessMode")
        if not isinstance(self.model_config, ModelConfig):
            raise InvalidAccessContextError("model_config must be a ModelConfig")
        if self.mode is LLMAccessMode.MANAGED:
            try:
                account_id = normalize_account_id(self.account_id)
                request_id = normalize_request_id(self.request_id)
            except Exception as error:
                raise InvalidAccessContextError(
                    "managed access requires account_id and request_id"
                ) from error
            object.__setattr__(self, "account_id", account_id)
            object.__setattr__(self, "request_id", request_id)
            return
        if self.account_id is not None:
            object.__setattr__(self, "account_id", normalize_account_id(self.account_id))
        if self.request_id is not None:
            object.__setattr__(self, "request_id", normalize_request_id(self.request_id))


def _normalize_non_empty(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InvalidUsageError(f"{field_name} must be a non-empty string")
    return value.strip()


def _validate_token_count(value: int, field_name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise InvalidUsageError(f"{field_name} must be a non-negative integer")
    return value


@dataclass(frozen=True)
class UsageRecord:
    provider_id: str
    model: str
    input_tokens: int
    output_tokens: int

    def __post_init__(self) -> None:
        provider_id = _normalize_non_empty(self.provider_id, "provider_id").lower()
        model = _normalize_non_empty(self.model, "model")
        input_tokens = _validate_token_count(self.input_tokens, "input_tokens")
        output_tokens = _validate_token_count(self.output_tokens, "output_tokens")
        if input_tokens == 0 and output_tokens == 0:
            raise InvalidUsageError("usage must contain at least one token")
        object.__setattr__(self, "provider_id", provider_id)
        object.__setattr__(self, "model", model)
        object.__setattr__(self, "input_tokens", input_tokens)
        object.__setattr__(self, "output_tokens", output_tokens)

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass(frozen=True)
class PricingContext:
    provider_id: str
    model: str
    max_input_tokens: int
    max_output_tokens: int

    def __post_init__(self) -> None:
        try:
            provider_id = _normalize_non_empty(self.provider_id, "provider_id").lower()
            model = _normalize_non_empty(self.model, "model")
            max_input_tokens = _validate_token_count(
                self.max_input_tokens, "max_input_tokens"
            )
            max_output_tokens = _validate_token_count(
                self.max_output_tokens, "max_output_tokens"
            )
        except InvalidUsageError as error:
            raise InvalidPricingContextError(str(error)) from None
        object.__setattr__(self, "provider_id", provider_id)
        object.__setattr__(self, "model", model)
        object.__setattr__(self, "max_input_tokens", max_input_tokens)
        object.__setattr__(self, "max_output_tokens", max_output_tokens)

    def to_dict(self) -> dict[str, str | int]:
        return {
            "provider_id": self.provider_id,
            "model": self.model,
            "max_input_tokens": self.max_input_tokens,
            "max_output_tokens": self.max_output_tokens,
        }


@dataclass(frozen=True)
class ManagedProviderResponse:
    content: str
    usage: UsageRecord | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.content, str):
            raise ManagedProviderError("managed provider content must be a string")
        if self.usage is not None and not isinstance(self.usage, UsageRecord):
            raise InvalidUsageError("usage must be a UsageRecord or None")


@dataclass(frozen=True)
class ManagedRequest:
    request_id: str
    account_id: str
    model_config: ModelConfig
    reserved_credits: int
    status: ManagedRequestStatus

    def __post_init__(self) -> None:
        object.__setattr__(self, "request_id", normalize_request_id(self.request_id))
        object.__setattr__(self, "account_id", normalize_account_id(self.account_id))
        if not isinstance(self.model_config, ModelConfig):
            raise ManagedAccessError("model_config must be a ModelConfig")
        validate_integer_amount(self.reserved_credits)
        if self.reserved_credits < 0:
            raise InvalidCreditAmountError("reserved_credits must be positive")
        if not isinstance(self.status, ManagedRequestStatus):
            raise ManagedAccessError("status must be a ManagedRequestStatus")


@dataclass(frozen=True)
class ManagedAccessResult:
    request_id: str
    account_id: str
    status: ManagedRequestStatus
    credits_charged: int
    replayed: bool
    content: str | None = field(default=None, repr=False)
    usage: UsageRecord | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "request_id", normalize_request_id(self.request_id))
        object.__setattr__(self, "account_id", normalize_account_id(self.account_id))
        if self.status is not ManagedRequestStatus.SUCCEEDED:
            raise ManagedAccessError("a result must represent a succeeded request")
        if (
            not isinstance(self.credits_charged, int)
            or isinstance(self.credits_charged, bool)
            or self.credits_charged < 0
        ):
            raise InvalidCreditAmountError(
                "credits_charged must be a non-negative integer"
            )
        if not isinstance(self.replayed, bool):
            raise ManagedAccessError("replayed must be a bool")
        if self.content is not None and not isinstance(self.content, str):
            raise ManagedAccessError("content must be a string or None")
        if self.usage is not None and not isinstance(self.usage, UsageRecord):
            raise InvalidUsageError("usage must be a UsageRecord or None")
