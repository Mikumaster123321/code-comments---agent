"""Optional, lazy-loaded local adapter for the frozen multilingual E5 model.

The module deliberately imports no ML package at module import time.  The core
``project_intelligence`` package therefore remains usable without the optional
embedding environment.  Real model loading is explicit (or happens on the
first embedding call) and never falls back to lexical retrieval.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from .domain import ProjectIntelligenceError
from .embedding import (
    DEFAULT_DOCUMENT_INSTRUCTION,
    DEFAULT_QUERY_INSTRUCTION,
    EmbeddingFingerprint,
    EmbeddingProvider,
    EmbeddingVector,
)


PRIMARY_MODEL_REPOSITORY = "intfloat/multilingual-e5-base"
PRIMARY_MODEL_REVISION = "d128750597153bb5987e10b1c3493a34e5a4502a"
PRIMARY_MODEL_DIMENSION = 768
MAX_INPUT_TOKENS = 512
MAX_INPUT_POLICY = "512-token-explicit-truncation-v1"


class LocalEmbeddingError(ProjectIntelligenceError):
    """Base error for the optional local embedding boundary."""


class EmbeddingDependencyError(LocalEmbeddingError):
    """Raised when the optional torch/transformers runtime is unavailable."""


class EmbeddingModelLoadError(LocalEmbeddingError):
    """Raised when the pinned tokenizer or model cannot be loaded."""


class EmbeddingTokenizationError(LocalEmbeddingError):
    """Raised when the real tokenizer cannot prepare an input."""


class EmbeddingInferenceError(LocalEmbeddingError):
    """Raised when model inference does not produce a valid embedding."""


@dataclass(frozen=True)
class TokenizationDiagnostic:
    """Token counts and explicit truncation status for one prepared input."""

    raw_token_count: int
    special_token_count: int
    total_token_count: int
    effective_content_limit: int
    truncated: bool


class LocalE5EmbeddingProvider:
    """A local ``transformers`` + ``torch`` implementation of ``EmbeddingProvider``.

    ``revision`` is explicit so experiments can compare identities, but the
    Phase 3.2 validation entry point uses :data:`PRIMARY_MODEL_REVISION`.  The
    device is an execution detail and is intentionally absent from the semantic
    fingerprint; the default CPU path is the reproducibility baseline.
    """

    def __init__(
        self,
        *,
        repository: str = PRIMARY_MODEL_REPOSITORY,
        revision: str = PRIMARY_MODEL_REVISION,
        device: str = "cpu",
        cache_dir: str | Path | None = None,
        model_path: str | Path | None = None,
        local_files_only: bool = False,
        batch_size: int = 8,
    ) -> None:
        if not isinstance(repository, str) or not repository:
            raise ValueError("repository must be a non-empty string")
        if not isinstance(revision, str) or not revision:
            raise ValueError("revision must be a non-empty string")
        if not isinstance(device, str) or not device:
            raise ValueError("device must be a non-empty string")
        if type(batch_size) is not int or batch_size <= 0:
            raise ValueError("batch_size must be a positive integer")
        self._repository = repository
        self._revision = revision
        self._device_name = device
        self._cache_dir = str(cache_dir) if cache_dir is not None else None
        self._model_path = str(model_path) if model_path is not None else None
        self._local_files_only = bool(local_files_only)
        self._batch_size = batch_size
        self._fingerprint = EmbeddingFingerprint(
            runtime_kind="transformers-torch",
            model_repository=repository,
            revision=revision,
            dimension=PRIMARY_MODEL_DIMENSION,
            normalization="l2",
            similarity_metric="cosine",
            query_instruction=DEFAULT_QUERY_INSTRUCTION,
            document_instruction=DEFAULT_DOCUMENT_INSTRUCTION,
            max_input_policy=MAX_INPUT_POLICY,
        )
        self._tokenizer: Any | None = None
        self._model: Any | None = None
        self._torch: Any | None = None
        self._last_diagnostics: tuple[TokenizationDiagnostic, ...] = ()

    @property
    def fingerprint(self) -> EmbeddingFingerprint:
        return self._fingerprint

    @property
    def device(self) -> str:
        """Configured execution device, not part of semantic identity."""

        return self._device_name

    @property
    def loaded(self) -> bool:
        return self._model is not None and self._tokenizer is not None

    @property
    def last_diagnostics(self) -> tuple[TokenizationDiagnostic, ...]:
        return self._last_diagnostics

    def load(self) -> None:
        """Load the pinned tokenizer and model explicitly, without network fallback."""

        if self.loaded:
            return
        try:
            import torch  # type: ignore[import-not-found]
            from transformers import AutoModel, AutoTokenizer  # type: ignore[import-not-found]
        except ImportError as error:
            raise EmbeddingDependencyError(
                "optional local embedding runtime is unavailable; install the pinned embedding requirements"
            ) from error

        try:
            device = torch.device(self._device_name)
            if device.type == "mps" and not torch.backends.mps.is_available():
                raise RuntimeError("requested device is unavailable")
            source = self._model_path or self._repository
            kwargs = {
                "cache_dir": self._cache_dir,
                "local_files_only": self._local_files_only,
            }
            if self._model_path is None:
                kwargs["revision"] = self._revision
            tokenizer = AutoTokenizer.from_pretrained(source, use_fast=True, **kwargs)
            model = AutoModel.from_pretrained(source, **kwargs)
            resolved_revision = getattr(getattr(model, "config", None), "_commit_hash", None)
            if resolved_revision is not None and resolved_revision != self._revision:
                raise RuntimeError("resolved model revision differs from requested revision")
            hidden_size = getattr(getattr(model, "config", None), "hidden_size", None)
            if hidden_size != self._fingerprint.dimension:
                raise RuntimeError("model hidden dimension differs from frozen contract")
            if getattr(tokenizer, "model_max_length", None) != MAX_INPUT_TOKENS:
                raise RuntimeError("tokenizer maximum length differs from frozen contract")
            model.to(device)
            model.eval()
        except LocalEmbeddingError:
            raise
        except Exception as error:
            # Keep cache paths, source text, and provider internals out of the
            # stable public error surface.
            raise EmbeddingModelLoadError(
                f"unable to load pinned local embedding model: {type(error).__name__}"
            ) from error

        self._torch = torch
        self._tokenizer = tokenizer
        self._model = model

    def diagnose(self, text: str, *, kind: str = "document") -> TokenizationDiagnostic:
        """Return real-tokenizer counts, including special-token truncation."""

        if not isinstance(text, str):
            raise EmbeddingTokenizationError("text must be a string")
        if not text.strip():
            raise EmbeddingTokenizationError("text must not be empty or whitespace")
        if kind not in {"query", "document"}:
            raise ValueError("kind must be 'query' or 'document'")
        self.load()
        assert self._tokenizer is not None
        prepared = self._prepare_text(text, kind)
        try:
            # The fast tokenizer backend gives unbounded counts without the
            # user-facing "sequence longer than max length" warning.  Actual
            # inference below still uses the public tokenizer with explicit
            # truncation at exactly 512 tokens.
            backend = getattr(self._tokenizer, "backend_tokenizer", None)
            if backend is None:
                raise RuntimeError("fast tokenizer backend is unavailable")
            previous_truncation = backend.truncation
            backend.no_truncation()
            try:
                raw = backend.encode(prepared, add_special_tokens=False).ids
                full = backend.encode(prepared, add_special_tokens=True).ids
            finally:
                if previous_truncation is None:
                    backend.no_truncation()
                else:
                    backend.enable_truncation(**previous_truncation)
        except Exception as error:
            raise EmbeddingTokenizationError(
                f"tokenizer failed to inspect input: {type(error).__name__}"
            ) from error
        raw_count = len(raw)
        total_count = len(full)
        special_count = max(0, total_count - raw_count)
        return TokenizationDiagnostic(
            raw_token_count=raw_count,
            special_token_count=special_count,
            total_token_count=total_count,
            effective_content_limit=max(0, MAX_INPUT_TOKENS - special_count),
            truncated=total_count > MAX_INPUT_TOKENS,
        )

    def embed_query(self, text: str) -> EmbeddingVector:
        return self._embed_batch((text,), kind="query")[0]

    def embed_documents(self, texts: Sequence[str]) -> tuple[EmbeddingVector, ...]:
        if not isinstance(texts, Sequence):
            raise EmbeddingTokenizationError("texts must be a sequence of strings")
        if not texts:
            self._last_diagnostics = ()
            return ()
        return self._embed_batch(tuple(texts), kind="document")

    def _prepare_text(self, text: str, kind: str) -> str:
        instruction = (
            self._fingerprint.query_instruction
            if kind == "query"
            else self._fingerprint.document_instruction
        )
        return text if text.startswith(instruction) else instruction + text

    def _embed_batch(self, texts: tuple[str, ...], *, kind: str) -> tuple[EmbeddingVector, ...]:
        if any(not isinstance(text, str) for text in texts):
            raise EmbeddingTokenizationError("texts must contain only strings")
        if any(not text.strip() for text in texts):
            raise EmbeddingTokenizationError("texts must not contain empty or whitespace values")
        self.load()
        assert self._tokenizer is not None and self._model is not None and self._torch is not None
        diagnostics = tuple(self.diagnose(text, kind=kind) for text in texts)
        self._last_diagnostics = diagnostics
        prepared = tuple(self._prepare_text(text, kind) for text in texts)
        vectors: list[EmbeddingVector] = []
        try:
            for start in range(0, len(prepared), self._batch_size):
                batch = prepared[start : start + self._batch_size]
                encoded = self._tokenizer(
                    list(batch),
                    padding=True,
                    truncation=True,
                    max_length=MAX_INPUT_TOKENS,
                    return_attention_mask=True,
                    return_tensors="pt",
                )
                encoded = {name: value.to(self._device_name) for name, value in encoded.items()}
                with self._torch.inference_mode():
                    output = self._model(**encoded)
                hidden = output.last_hidden_state
                mask = encoded["attention_mask"].unsqueeze(-1).to(hidden.dtype)
                pooled = (hidden * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)
                norms = self._torch.linalg.vector_norm(pooled, dim=1, keepdim=True)
                if self._torch.any(norms == 0) or not bool(self._torch.isfinite(pooled).all()):
                    raise RuntimeError("model output is non-finite or zero")
                normalized = pooled / norms
                for row in normalized.detach().to("cpu").tolist():
                    vector = EmbeddingVector(row, self._fingerprint.dimension)
                    norm = math.sqrt(math.fsum(value * value for value in vector.values))
                    if not math.isfinite(norm) or norm == 0:
                        raise RuntimeError("normalized output is invalid")
                    vectors.append(vector)
        except (EmbeddingTokenizationError, EmbeddingInferenceError):
            raise
        except Exception as error:
            raise EmbeddingInferenceError(
                f"local embedding inference failed: {type(error).__name__}"
            ) from error
        return tuple(vectors)


__all__ = [
    "EmbeddingDependencyError",
    "EmbeddingInferenceError",
    "EmbeddingModelLoadError",
    "EmbeddingTokenizationError",
    "LocalE5EmbeddingProvider",
    "LocalEmbeddingError",
    "MAX_INPUT_POLICY",
    "MAX_INPUT_TOKENS",
    "PRIMARY_MODEL_DIMENSION",
    "PRIMARY_MODEL_REPOSITORY",
    "PRIMARY_MODEL_REVISION",
    "TokenizationDiagnostic",
]
