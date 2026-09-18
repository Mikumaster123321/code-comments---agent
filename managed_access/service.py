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
    InvalidPricingContextError,
    InvalidUsageError,
    ManagedAccessError,
    ManagedAccessResult,
    ManagedFinalizationError,
    ManagedProviderError,
    ManagedProviderResponse,
    ManagedRequest,
    ManagedRequestConflictError,
    ManagedRequestFailedError,
    ManagedRequestRecoveryRequiredError,
    ManagedRequestStatus,
    PricingContext,
    UsageRecord,
)
from .pricing import FlatPricingPolicy, InvalidFlatPricingError, PricingPolicy


FaultInjector = Callable[[str], None]
_USAGE_NOTE = "managed access usage"


@runtime_checkable
class ManagedProvider(Protocol):
    def invoke(
        self, *, model_config: ModelConfig, prompt: str
    ) -> str | ManagedProviderResponse: ...


class ManagedAccessService:
    """Backend-facing coordinator for one offline-testable Managed request loop."""

    def __init__(
        self,
        database: str | Path,
        provider: ManagedProvider,
        pricing_policy: PricingPolicy,
        *,
        fault_injector: FaultInjector | None = None,
    ) -> None:
        if not isinstance(provider, ManagedProvider):
            raise TypeError("provider must implement ManagedProvider")
        if not isinstance(pricing_policy, PricingPolicy):
            raise TypeError("pricing_policy must implement PricingPolicy")
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

    def invoke(
        self,
        context: LLMAccessContext,
        prompt: str,
        *,
        pricing_context: PricingContext | None = None,
    ) -> ManagedAccessResult:
        if not isinstance(context, LLMAccessContext):
            raise TypeError("context must be an LLMAccessContext")
        if context.mode is not LLMAccessMode.MANAGED:
            raise ManagedAccessError("ManagedAccessService requires MANAGED mode")
        if not isinstance(prompt, str):
            raise TypeError("prompt must be a string")

        pricing_context = self._resolve_pricing_context(context, pricing_context)
        reserved_credits = self.__pricing_policy.reserve_credits(pricing_context)
        if (
            not isinstance(reserved_credits, int)
            or isinstance(reserved_credits, bool)
            or reserved_credits <= 0
        ):
            raise InvalidPricingContextError(
                "pricing policy must return a positive integer reservation"
            )
        payload_hash = self._payload_hash(
            context.model_config,
            prompt,
            pricing_context,
            self.__pricing_policy.policy_id,
            reserved_credits,
        )
        request, created = self._reserve(
            context, prompt, pricing_context, reserved_credits, payload_hash
        )
        if not created:
            return self._replay(request)

        try:
            self._inject("after_reservation_commit")
        except Exception:
            raise ManagedRequestRecoveryRequiredError(
                "managed request is reserved and requires reconciliation"
            ) from None

        provider_succeeded, content, usage = self._invoke_provider(
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

        try:
            if usage is not None:
                if not isinstance(usage, UsageRecord):
                    raise InvalidUsageError("provider usage is malformed")
                usage = UsageRecord(
                    provider_id=usage.provider_id,
                    model=usage.model,
                    input_tokens=usage.input_tokens,
                    output_tokens=usage.output_tokens,
                )
            actual_credits = self.__pricing_policy.price_usage(
                pricing_context, usage
            )
            if (
                not isinstance(actual_credits, int)
                or isinstance(actual_credits, bool)
                or actual_credits < 0
                or actual_credits > reserved_credits
            ):
                raise InvalidUsageError(
                    "actual credits must be within the reserved upper bound"
                )
        except Exception:
            self._try_mark_finalization_failed(
                context.account_id, context.request_id
            )
            raise ManagedFinalizationError(
                "provider succeeded but usage requires reconciliation"
            ) from None

        if not self._try_finalize_success(
            context.account_id,
            context.request_id,
            actual_credits,
            usage,
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
            credits_charged=actual_credits,
            replayed=False,
            content=content,
            usage=usage,
        )

    def _invoke_provider(
        self, model_config: ModelConfig, prompt: str
    ) -> tuple[bool, str | None, UsageRecord | None]:
        try:
            response = self.__provider.invoke(
                model_config=model_config,
                prompt=prompt,
            )
        except Exception:
            return False, None, None
        if isinstance(response, str):
            return True, response, None
        if isinstance(response, ManagedProviderResponse):
            return True, response.content, response.usage
        return False, None, None

    def _try_mark_provider_failed(self, account_id: str, request_id: str) -> bool:
        try:
            self._mark_provider_failed(account_id, request_id)
        except Exception:
            return False
        return True

    def _try_finalize_success(
        self,
        account_id: str,
        request_id: str,
        actual_credits: int,
        usage: UsageRecord | None,
    ) -> bool:
        try:
            self._finalize_success(
                account_id, request_id, actual_credits, usage
            )
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
        prompt: str,
        pricing_context: PricingContext,
        reserved_credits: int,
        payload_hash: str,
    ) -> tuple[ManagedRequest, bool]:
        try:
            with self._write_transaction() as connection:
                row = self._request_row(
                    connection, context.account_id, context.request_id
                )
                if row is not None:
                    request = self._request_from_row(row)
                    expected_hash = payload_hash
                    if int(row[9]) == 1:
                        expected_hash = self._legacy_payload_hash(
                            context.model_config, prompt, reserved_credits
                        )
                    if (
                        str(row[7]) != expected_hash
                        or str(row[8]) != self.__pricing_policy.policy_id
                        or int(row[10]) != pricing_context.max_input_tokens
                        or int(row[11]) != pricing_context.max_output_tokens
                    ):
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
                if available < reserved_credits:
                    raise InsufficientCreditsError("insufficient available credits")

                connection.execute(
                    """
                    INSERT INTO managed_requests (
                        account_id, request_id, provider_id, model, base_url,
                        reserved_credits, status, payload_hash, pricing_policy_id,
                        payload_version, max_input_tokens, max_output_tokens
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        context.account_id,
                        context.request_id,
                        context.model_config.provider_id,
                        context.model_config.model,
                        context.model_config.base_url,
                        reserved_credits,
                        ManagedRequestStatus.RESERVED.value,
                        payload_hash,
                        self.__pricing_policy.policy_id,
                        2,
                        pricing_context.max_input_tokens,
                        pricing_context.max_output_tokens,
                    ),
                )
                self._inject("before_reservation_commit")
                return (
                    ManagedRequest(
                        request_id=context.request_id,
                        account_id=context.account_id,
                        model_config=context.model_config,
                        reserved_credits=reserved_credits,
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
            final_credits, usage = self._success_metadata(
                request.account_id, request.request_id, request.reserved_credits
            )
            return ManagedAccessResult(
                request_id=request.request_id,
                account_id=request.account_id,
                status=request.status,
                credits_charged=final_credits,
                replayed=True,
                content=None,
                usage=usage,
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
            cursor = connection.execute(
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
            if cursor.rowcount != 1:
                raise ManagedAccessError("request is not reserved")

    def _finalize_success(
        self,
        account_id: str,
        request_id: str,
        actual_credits: int,
        usage: UsageRecord | None,
    ) -> None:
        with self._write_transaction() as connection:
            row = self._request_row(connection, account_id, request_id)
            if (
                row is None
                or ManagedRequestStatus(str(row[6]))
                is not ManagedRequestStatus.RESERVED
            ):
                raise ManagedAccessError("request is not reserved")
            reserved_credits = int(row[5])
            if actual_credits < 0 or actual_credits > reserved_credits:
                raise ManagedAccessError("actual credits exceed the reservation")

            existing = SQLiteCreditLedger._idempotent_transaction(
                connection, TransactionType.USAGE, account_id, request_id
            )
            if actual_credits == 0:
                if existing is not None:
                    raise ManagedAccessError("zero-cost request has an existing charge")
            elif existing is None:
                if SQLiteCreditLedger._balance(connection, account_id) < actual_credits:
                    raise InsufficientCreditsError("insufficient credits during finalization")
                self._inject("before_usage_append")
                transaction = SQLiteCreditLedger._append_transaction(
                    connection,
                    account_id=account_id,
                    transaction_type=TransactionType.USAGE,
                    amount=-actual_credits,
                    request_id=request_id,
                    note=_USAGE_NOTE,
                )
                self._inject("after_usage_append_before_idempotency_commit")
                SQLiteCreditLedger._append_idempotency_record(connection, transaction)
            else:
                SQLiteCreditLedger._resolve_idempotent_retry(
                    existing, -actual_credits, _USAGE_NOTE
                )

            self._inject("before_usage_metadata_write")
            connection.execute(
                """
                INSERT INTO managed_usage (
                    account_id, request_id, provider_id, model,
                    input_tokens, output_tokens, final_credits
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    account_id,
                    request_id,
                    None if usage is None else usage.provider_id,
                    None if usage is None else usage.model,
                    None if usage is None else usage.input_tokens,
                    None if usage is None else usage.output_tokens,
                    actual_credits,
                ),
            )
            self._inject("after_usage_metadata_write")

            self._inject("before_request_success_update")
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
                    pricing_policy_id TEXT NOT NULL,
                    payload_version INTEGER NOT NULL,
                    max_input_tokens INTEGER NOT NULL,
                    max_output_tokens INTEGER NOT NULL,
                    PRIMARY KEY (account_id, request_id)
                )
                """
            )
            columns = {
                str(row[1])
                for row in self._connection.execute(
                    "PRAGMA table_info(managed_requests)"
                )
            }
            migrations = (
                ("pricing_policy_id", "TEXT NOT NULL DEFAULT ''"),
                ("payload_version", "INTEGER NOT NULL DEFAULT 1"),
                ("max_input_tokens", "INTEGER NOT NULL DEFAULT 0"),
                ("max_output_tokens", "INTEGER NOT NULL DEFAULT 0"),
            )
            for column, definition in migrations:
                if column not in columns:
                    self._connection.execute(
                        f"ALTER TABLE managed_requests ADD COLUMN {column} {definition}"
                    )
            self._connection.execute(
                """
                UPDATE managed_requests
                SET pricing_policy_id = 'flat:v1:' || reserved_credits
                WHERE pricing_policy_id = ''
                """
            )
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS managed_usage (
                    account_id TEXT NOT NULL,
                    request_id TEXT NOT NULL,
                    provider_id TEXT,
                    model TEXT,
                    input_tokens INTEGER CHECK (
                        input_tokens IS NULL OR input_tokens >= 0
                    ),
                    output_tokens INTEGER CHECK (
                        output_tokens IS NULL OR output_tokens >= 0
                    ),
                    final_credits INTEGER NOT NULL CHECK (final_credits >= 0),
                    PRIMARY KEY (account_id, request_id),
                    FOREIGN KEY (account_id, request_id)
                        REFERENCES managed_requests(account_id, request_id)
                        ON DELETE RESTRICT,
                    CHECK (
                        (provider_id IS NULL AND model IS NULL
                            AND input_tokens IS NULL AND output_tokens IS NULL)
                        OR
                        (provider_id IS NOT NULL AND model IS NOT NULL
                            AND input_tokens IS NOT NULL AND output_tokens IS NOT NULL)
                    )
                )
                """
            )
            self._connection.execute(
                """
                INSERT OR IGNORE INTO managed_usage (
                    account_id, request_id, provider_id, model,
                    input_tokens, output_tokens, final_credits
                )
                SELECT account_id, request_id, NULL, NULL, NULL, NULL,
                       reserved_credits
                FROM managed_requests
                WHERE status = ?
                """,
                (ManagedRequestStatus.SUCCEEDED.value,),
            )

    @staticmethod
    def _request_row(
        connection: sqlite3.Connection, account_id: str, request_id: str
    ) -> tuple[object, ...] | None:
        return connection.execute(
            """
            SELECT request_id, account_id, provider_id, model, base_url,
                   reserved_credits, status, payload_hash, pricing_policy_id,
                   payload_version, max_input_tokens, max_output_tokens
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
    def _payload_hash(
        model_config: ModelConfig,
        prompt: str,
        pricing_context: PricingContext,
        policy_id: str,
        reserved_credits: int,
    ) -> str:
        payload = {
            "model_config": model_config.to_dict(),
            "prompt": prompt,
            "pricing_context": pricing_context.to_dict(),
            "pricing_policy_id": policy_id,
            "reserved_credits": reserved_credits,
        }
        encoded = json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    @staticmethod
    def _legacy_payload_hash(
        model_config: ModelConfig, prompt: str, cost: int
    ) -> str:
        payload = {
            "model_config": model_config.to_dict(),
            "prompt": prompt,
            "reserved_credits": cost,
        }
        encoded = json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    @staticmethod
    def _resolve_pricing_context(
        context: LLMAccessContext,
        pricing_context: PricingContext | None,
    ) -> PricingContext:
        if pricing_context is None:
            pricing_context = PricingContext(
                provider_id=context.model_config.provider_id,
                model=context.model_config.model,
                max_input_tokens=0,
                max_output_tokens=0,
            )
        if not isinstance(pricing_context, PricingContext):
            raise TypeError("pricing_context must be a PricingContext or None")
        if (
            pricing_context.provider_id != context.model_config.provider_id
            or pricing_context.model != context.model_config.model
        ):
            raise InvalidPricingContextError(
                "pricing context must match the managed model selection"
            )
        return pricing_context

    def _success_metadata(
        self, account_id: str, request_id: str, fallback_credits: int
    ) -> tuple[int, UsageRecord | None]:
        with self._lock:
            row = self._connection.execute(
                """
                SELECT provider_id, model, input_tokens, output_tokens, final_credits
                FROM managed_usage
                WHERE account_id = ? AND request_id = ?
                """,
                (account_id, request_id),
            ).fetchone()
        if row is None:
            return fallback_credits, None
        if row[0] is None:
            return int(row[4]), None
        return int(row[4]), UsageRecord(
            provider_id=str(row[0]),
            model=str(row[1]),
            input_tokens=int(row[2]),
            output_tokens=int(row[3]),
        )

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
