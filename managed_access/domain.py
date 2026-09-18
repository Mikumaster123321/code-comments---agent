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

    def __post_init__(self) -> None:
        object.__setattr__(self, "request_id", normalize_request_id(self.request_id))
        object.__setattr__(self, "account_id", normalize_account_id(self.account_id))
        if self.status is not ManagedRequestStatus.SUCCEEDED:
            raise ManagedAccessError("a result must represent a succeeded request")
        validate_integer_amount(self.credits_charged)
        if self.credits_charged < 0:
            raise InvalidCreditAmountError("credits_charged must be positive")
        if not isinstance(self.replayed, bool):
            raise ManagedAccessError("replayed must be a bool")
        if self.content is not None and not isinstance(self.content, str):
            raise ManagedAccessError("content must be a string or None")
