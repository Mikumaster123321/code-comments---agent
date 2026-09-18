from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from threading import RLock
from typing import Callable, Protocol, runtime_checkable

from credits import InsufficientCreditsError, TransactionType
from credits.sqlite_ledger import SQLiteCreditLedger
from llm_provider import ModelConfig

from .domain import (
    LLMAccessContext,
    LLMAccessMode,
    ManagedAccessError,
    ManagedAccessResult,
    ManagedFinalizationError,
    ManagedProviderError,
    ManagedRequest,
    ManagedRequestConflictError,
    ManagedRequestFailedError,
    ManagedRequestRecoveryRequiredError,
    ManagedRequestStatus,
)


FaultInjector = Callable[[str], None]
_USAGE_NOTE = "managed access usage"


class InvalidFlatPricingError(ValueError):
    """Raised when the flat request price is not a positive integer."""


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

    def credits_for(self, model_config: ModelConfig) -> int:
        if not isinstance(model_config, ModelConfig):
            raise TypeError("model_config must be a ModelConfig")
        return self._credits_per_request


@runtime_checkable
class ManagedProvider(Protocol):
    def invoke(self, *, model_config: ModelConfig, prompt: str) -> str: ...


class ManagedAccessService:
    """Backend-facing coordinator for one offline-testable Managed request loop."""

    def __init__(
        self,
        database: str | Path,
        provider: ManagedProvider,
        pricing_policy: FlatPricingPolicy,
        *,
        fault_injector: FaultInjector | None = None,
    ) -> None:
        if not isinstance(provider, ManagedProvider):
            raise TypeError("provider must implement ManagedProvider")
        if not isinstance(pricing_policy, FlatPricingPolicy):
            raise TypeError("pricing_policy must be a FlatPricingPolicy")
        self.__provider = provider
        self.__pricing_policy = pricing_policy
        self._fault_injector = fault_injector
        self._lock = RLock()
        self._connection = sqlite3.connect(
            str(database),
            timeout=30,
            isolation_level=None,
            check_same_thread=False,
        )
        SQLiteCreditLedger._configure_connection(self._connection)
        SQLiteCreditLedger._initialize_schema(self._connection)
        self._initialize_schema()

    def __repr__(self) -> str:
        return "ManagedAccessService(<server-side provider boundary>)"

    def close(self) -> None:
        with self._lock:
            self._connection.close()

    def invoke(self, context: LLMAccessContext, prompt: str) -> ManagedAccessResult:
        if not isinstance(context, LLMAccessContext):
            raise TypeError("context must be an LLMAccessContext")
        if context.mode is not LLMAccessMode.MANAGED:
            raise ManagedAccessError("ManagedAccessService requires MANAGED mode")
        if not isinstance(prompt, str):
            raise TypeError("prompt must be a string")

        cost = self.__pricing_policy.credits_for(context.model_config)
        payload_hash = self._payload_hash(context.model_config, prompt, cost)
        request, created = self._reserve(context, cost, payload_hash)
        if not created:
            return self._replay(request)

        try:
            self._inject("after_reservation_commit")
        except Exception:
            raise ManagedRequestRecoveryRequiredError(
                "managed request is reserved and requires reconciliation"
            ) from None

        provider_succeeded, content = self._invoke_provider(
            context.model_config, prompt
        )
        if not provider_succeeded:
            if not self._try_mark_provider_failed(
                context.account_id, context.request_id
            ):
                raise ManagedRequestRecoveryRequiredError(
                    "provider failed and request state requires reconciliation"
                )
            raise ManagedProviderError("managed provider request failed")

        if not self._try_finalize_success(
            context.account_id, context.request_id, cost
        ):
            self._try_mark_finalization_failed(
                context.account_id, context.request_id
            )
            raise ManagedFinalizationError(
                "provider succeeded but accounting requires reconciliation"
            )

        return ManagedAccessResult(
            request_id=context.request_id,
            account_id=context.account_id,
            status=ManagedRequestStatus.SUCCEEDED,
            credits_charged=cost,
            replayed=False,
            content=content,
        )

    def _invoke_provider(
        self, model_config: ModelConfig, prompt: str
    ) -> tuple[bool, str | None]:
        try:
            content = self.__provider.invoke(
                model_config=model_config,
                prompt=prompt,
            )
        except Exception:
            return False, None
        if not isinstance(content, str):
            return False, None
        return True, content

    def _try_mark_provider_failed(self, account_id: str, request_id: str) -> bool:
        try:
            self._mark_provider_failed(account_id, request_id)
        except Exception:
            return False
        return True

    def _try_finalize_success(
        self, account_id: str, request_id: str, cost: int
    ) -> bool:
        try:
            self._finalize_success(account_id, request_id, cost)
        except Exception:
            return False
        return True

    def _try_mark_finalization_failed(
        self, account_id: str, request_id: str
    ) -> bool:
        try:
            self._mark_finalization_failed(account_id, request_id)
        except Exception:
            return False
        return True

    def get_request(self, account_id: str, request_id: str) -> ManagedRequest | None:
        from credits.domain import normalize_account_id, normalize_request_id

        account_id = normalize_account_id(account_id)
        request_id = normalize_request_id(request_id)
        with self._lock:
            row = self._request_row(self._connection, account_id, request_id)
        return None if row is None else self._request_from_row(row)

    def _reserve(
        self,
        context: LLMAccessContext,
        cost: int,
        payload_hash: str,
    ) -> tuple[ManagedRequest, bool]:
        try:
            with self._write_transaction() as connection:
                row = self._request_row(
                    connection, context.account_id, context.request_id
                )
                if row is not None:
                    request = self._request_from_row(row)
                    if str(row[7]) != payload_hash:
                        raise ManagedRequestConflictError(
                            "request_id was already used with a different payload"
                        )
                    return request, False

                balance = SQLiteCreditLedger._balance(connection, context.account_id)
                reserved_row = connection.execute(
                    """
                    SELECT COALESCE(SUM(reserved_credits), 0)
                    FROM managed_requests
                    WHERE account_id = ? AND status IN (?, ?)
                    """,
                    (
                        context.account_id,
                        ManagedRequestStatus.RESERVED.value,
                        ManagedRequestStatus.FINALIZATION_FAILED.value,
                    ),
                ).fetchone()
                available = balance - int(reserved_row[0])
                if available < cost:
                    raise InsufficientCreditsError("insufficient available credits")

                connection.execute(
                    """
                    INSERT INTO managed_requests (
                        account_id, request_id, provider_id, model, base_url,
                        reserved_credits, status, payload_hash
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        context.account_id,
                        context.request_id,
                        context.model_config.provider_id,
                        context.model_config.model,
                        context.model_config.base_url,
                        cost,
                        ManagedRequestStatus.RESERVED.value,
                        payload_hash,
                    ),
                )
                self._inject("before_reservation_commit")
                return (
                    ManagedRequest(
                        request_id=context.request_id,
                        account_id=context.account_id,
                        model_config=context.model_config,
                        reserved_credits=cost,
                        status=ManagedRequestStatus.RESERVED,
                    ),
                    True,
                )
        except (InsufficientCreditsError, ManagedRequestConflictError):
            raise
        except Exception:
            raise ManagedAccessError("managed request could not be reserved") from None

    def _replay(self, request: ManagedRequest) -> ManagedAccessResult:
        if request.status is ManagedRequestStatus.SUCCEEDED:
            return ManagedAccessResult(
                request_id=request.request_id,
                account_id=request.account_id,
                status=request.status,
                credits_charged=request.reserved_credits,
                replayed=True,
                content=None,
            )
        if request.status is ManagedRequestStatus.FAILED:
            raise ManagedRequestFailedError(
                "managed request previously failed and is terminal"
            )
        if request.status is ManagedRequestStatus.FINALIZATION_FAILED:
            raise ManagedFinalizationError(
                "provider already succeeded; accounting requires reconciliation"
            )
        raise ManagedRequestRecoveryRequiredError(
            "managed request is already reserved or in progress"
        )

    def _mark_provider_failed(self, account_id: str, request_id: str) -> None:
        with self._write_transaction() as connection:
            cursor = connection.execute(
                """
                UPDATE managed_requests SET status = ?
                WHERE account_id = ? AND request_id = ? AND status = ?
                """,
                (
                    ManagedRequestStatus.FAILED.value,
                    account_id,
                    request_id,
                    ManagedRequestStatus.RESERVED.value,
                ),
            )
            if cursor.rowcount != 1:
                raise ManagedAccessError("request is not reserved")

    def _mark_finalization_failed(self, account_id: str, request_id: str) -> None:
        with self._write_transaction() as connection:
            connection.execute(
                """
                UPDATE managed_requests SET status = ?
                WHERE account_id = ? AND request_id = ? AND status = ?
                """,
                (
                    ManagedRequestStatus.FINALIZATION_FAILED.value,
                    account_id,
                    request_id,
                    ManagedRequestStatus.RESERVED.value,
                ),
            )

    def _finalize_success(self, account_id: str, request_id: str, cost: int) -> None:
        with self._write_transaction() as connection:
            row = self._request_row(connection, account_id, request_id)
            if (
                row is None
                or ManagedRequestStatus(str(row[6]))
                is not ManagedRequestStatus.RESERVED
            ):
                raise ManagedAccessError("request is not reserved")

            existing = SQLiteCreditLedger._idempotent_transaction(
                connection, TransactionType.USAGE, account_id, request_id
            )
            if existing is None:
                if SQLiteCreditLedger._balance(connection, account_id) < cost:
                    raise InsufficientCreditsError("insufficient credits during finalization")
                self._inject("before_usage_append")
                transaction = SQLiteCreditLedger._append_transaction(
                    connection,
                    account_id=account_id,
                    transaction_type=TransactionType.USAGE,
                    amount=-cost,
                    request_id=request_id,
                    note=_USAGE_NOTE,
                )
                self._inject("after_usage_append_before_idempotency_commit")
                SQLiteCreditLedger._append_idempotency_record(connection, transaction)
            else:
                SQLiteCreditLedger._resolve_idempotent_retry(
                    existing, -cost, _USAGE_NOTE
                )

            cursor = connection.execute(
                """
                UPDATE managed_requests SET status = ?
                WHERE account_id = ? AND request_id = ? AND status = ?
                """,
                (
                    ManagedRequestStatus.SUCCEEDED.value,
                    account_id,
                    request_id,
                    ManagedRequestStatus.RESERVED.value,
                ),
            )
            if cursor.rowcount != 1:
                raise ManagedAccessError("request final status could not be persisted")
            self._inject("before_request_final_status_commit")

    def _initialize_schema(self) -> None:
        with self._lock:
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS managed_requests (
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

    @staticmethod
    def _request_row(
        connection: sqlite3.Connection, account_id: str, request_id: str
    ) -> tuple[object, ...] | None:
        return connection.execute(
            """
            SELECT request_id, account_id, provider_id, model, base_url,
                   reserved_credits, status, payload_hash
            FROM managed_requests
            WHERE account_id = ? AND request_id = ?
            """,
            (account_id, request_id),
        ).fetchone()

    @staticmethod
    def _request_from_row(row: tuple[object, ...]) -> ManagedRequest:
        return ManagedRequest(
            request_id=str(row[0]),
            account_id=str(row[1]),
            model_config=ModelConfig(str(row[2]), str(row[3]), str(row[4])),
            reserved_credits=int(row[5]),
            status=ManagedRequestStatus(str(row[6])),
        )

    @staticmethod
    def _payload_hash(model_config: ModelConfig, prompt: str, cost: int) -> str:
        payload = {
            "model_config": model_config.to_dict(),
            "prompt": prompt,
            "reserved_credits": cost,
        }
        encoded = json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def _inject(self, point: str) -> None:
        if self._fault_injector is not None:
            self._fault_injector(point)

    class _WriteTransaction:
        def __init__(self, service: ManagedAccessService) -> None:
            self._service = service

        def __enter__(self) -> sqlite3.Connection:
            self._service._lock.acquire()
            try:
                self._service._connection.execute("BEGIN IMMEDIATE")
            except BaseException:
                self._service._lock.release()
                raise
            return self._service._connection

        def __exit__(self, error_type, _error, _traceback) -> bool:
            try:
                if error_type is None:
                    try:
                        self._service._connection.commit()
                    except BaseException:
                        self._service._connection.rollback()
                        raise
                else:
                    self._service._connection.rollback()
            finally:
                self._service._lock.release()
            return False

    def _write_transaction(self) -> ManagedAccessService._WriteTransaction:
        return self._WriteTransaction(self)
