"""Deterministic, standard-library-only BM25 lexical retrieval.

This module intentionally implements a conventional BM25 baseline rather than a
new ranking algorithm.  For a document ``d`` and query term ``t`` the score is

``idf(t) * tf(t,d) * (k1 + 1) / (tf(t,d) + k1 * (1 - b + b * dl / avgdl))``

where ``N`` is the number of indexed documents, ``df(t)`` is the number of
documents containing ``t``, ``dl`` is document token length, ``avgdl`` is the
corpus average document length, and the frozen IDF is
``log(1 + (N - df(t) + 0.5) / (df(t) + 0.5))``.

The baseline tokenizes the qualified name once as symbol-identity enrichment
and the source text once.  Identifier tokens are retained alongside deterministic
components (for example ``ManagedAccessService`` produces
``managedaccessservice``, ``managed``, ``access``, and ``service``).  Source
comments and strings are intentionally part of this lexical baseline; no parser
or stop-word pipeline is involved.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping, Sequence

from code_maintenance.domain import SymbolId

from .domain import RetrievalDocument


TOKENIZER_VERSION = "code-lexical-v1"


class LexicalRetrievalError(Exception):
    """Base error for the lexical retrieval boundary."""


class InvalidLexicalQueryError(LexicalRetrievalError):
    """Raised when a query or ``top_k`` value is invalid."""


class InvalidBM25ConfigError(LexicalRetrievalError):
    """Raised when BM25 parameters are invalid or non-finite."""


class DuplicateLexicalDocumentError(LexicalRetrievalError):
    """Raised when the corpus contains the same authoritative SymbolId twice."""

    def __init__(self, symbol_id: SymbolId) -> None:
        super().__init__(f"duplicate lexical document: symbol='{symbol_id}'")
        self.symbol_id = symbol_id


@dataclass(frozen=True)
class BM25Config:
    """The explicit, immutable configuration for a BM25 index."""

    k1: float = 1.5
    b: float = 0.75
    tokenizer_version: str = TOKENIZER_VERSION

    def __post_init__(self) -> None:
        for name, value in (("k1", self.k1), ("b", self.b)):
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise InvalidBM25ConfigError(f"{name} must be a finite number")
            numeric = float(value)
            if not math.isfinite(numeric):
                raise InvalidBM25ConfigError(f"{name} must be finite")
            if name == "k1" and numeric <= 0:
                raise InvalidBM25ConfigError("k1 must be greater than zero")
            if name == "b" and not 0 <= numeric <= 1:
                raise InvalidBM25ConfigError("b must be between zero and one")
            object.__setattr__(self, name, numeric)
        if not isinstance(self.tokenizer_version, str) or not self.tokenizer_version:
            raise InvalidBM25ConfigError("tokenizer_version must be a non-empty string")
        if self.tokenizer_version != TOKENIZER_VERSION:
            raise InvalidBM25ConfigError(
                f"unsupported tokenizer_version: {self.tokenizer_version!r}"
            )


@dataclass(frozen=True)
class LexicalHit:
    """An immutable lexical result, ordered by rank then canonical SymbolId."""

    document: RetrievalDocument
    score: float
    rank: int

    @property
    def symbol_id(self) -> SymbolId:
        return self.document.symbol_id

    @property
    def document_id(self) -> SymbolId:
        """Alias exposing the authoritative document identity explicitly."""
        return self.document.symbol_id

    @property
    def content_hash(self) -> str:
        return self.document.content_hash


_WORD_RE = re.compile(r"[^\W_]+(?:_[^\W_]+)*", re.UNICODE)
_OPERATOR_RE = re.compile(r"(?:==|!=|<=|>=|->|//|\*\*|&&|\|\||<<|>>|[+\-*/%=<>!&|^~])")
_ASCII_SPLIT_RE = re.compile(
    r"(?<=[a-z0-9])(?=[A-Z])|"
    r"(?<=[A-Z])(?=[A-Z][a-z])|"
    r"(?<=[A-Za-z])(?=[0-9])|"
    r"(?<=[0-9])(?=[A-Za-z])"
)


def _identifier_parts(token: str) -> tuple[str, ...]:
    """Return lower-case identifier components using fixed ASCII case rules."""

    pieces: list[str] = []
    for underscore_piece in token.split("_"):
        if not underscore_piece:
            continue
        pieces.extend(part for part in _ASCII_SPLIT_RE.split(underscore_piece) if part)
    return tuple(piece.casefold() for piece in pieces if piece)


def tokenize(text: str) -> tuple[str, ...]:
    """Tokenize code/query text deterministically with Unicode ``casefold``.

    Words include Unicode letters/digits and underscore-connected identifiers.
    Each word contributes its case-folded original token and its split identifier
    parts.  Operators are retained as tokens; punctuation is otherwise a
    separator.  The same function is used for documents and queries.
    """

    if not isinstance(text, str):
        raise TypeError("text must be a string")
    tokens: list[str] = []
    occupied: list[tuple[int, int]] = []
    for match in _WORD_RE.finditer(text):
        raw = match.group(0).casefold()
        tokens.append(raw)
        tokens.extend(part for part in _identifier_parts(match.group(0)) if part != raw)
        occupied.append((match.start(), match.end()))

    # Operators are useful for code searches.  Avoid treating operators inside
    # word spans as separate tokens (the regexes do not overlap in practice).
    for match in _OPERATOR_RE.finditer(text):
        if not any(start <= match.start() < end for start, end in occupied):
            tokens.append(match.group(0).casefold())
    return tuple(tokens)


def _symbol_id_key(
    symbol_id: SymbolId,
) -> tuple[str, str, str, str, tuple[bool, str], tuple[bool, int]]:
    return (
        symbol_id.language,
        symbol_id.relative_path,
        symbol_id.qualified_name,
        symbol_id.kind.value,
        (symbol_id.semantic_disambiguator is None, symbol_id.semantic_disambiguator or ""),
        (symbol_id.fallback_line is None, symbol_id.fallback_line or 0),
    )


class BM25TextScorer:
    """Production BM25 scoring over caller-ordered text units."""

    def __init__(self, texts: Sequence[str], config: BM25Config = BM25Config()) -> None:
        if not isinstance(config, BM25Config):
            raise InvalidBM25ConfigError("config must be a BM25Config")
        if not all(isinstance(text, str) for text in texts):
            raise TypeError("texts must contain strings")
        self._config = config
        self._count = len(texts)
        token_counts: list[Mapping[str, int]] = []
        lengths: list[int] = []
        frequencies: dict[str, int] = {}
        for text in texts:
            counts: dict[str, int] = {}
            tokens = tokenize(text)
            for token in tokens:
                counts[token] = counts.get(token, 0) + 1
            token_counts.append(MappingProxyType(counts))
            lengths.append(len(tokens))
            for token in counts:
                frequencies[token] = frequencies.get(token, 0) + 1
        self._token_counts = tuple(token_counts)
        self._document_lengths = tuple(lengths)
        self._document_frequencies = MappingProxyType(dict(frequencies))
        self._average_document_length = sum(lengths) / len(lengths) if lengths else 0.0

    @property
    def average_document_length(self) -> float:
        return self._average_document_length

    @property
    def document_frequencies(self) -> Mapping[str, int]:
        return self._document_frequencies

    @property
    def document_lengths(self) -> tuple[int, ...]:
        return self._document_lengths

    def search(self, query: str, top_k: int = 10) -> tuple[tuple[int, float], ...]:
        if not isinstance(query, str):
            raise InvalidLexicalQueryError("query must be a string")
        if type(top_k) is not int or top_k <= 0:
            raise InvalidLexicalQueryError("top_k must be an integer greater than zero")
        if not query.strip() or not self._count or self._average_document_length == 0:
            return ()
        terms = tuple(dict.fromkeys(tokenize(query)))
        known_terms = tuple(term for term in terms if term in self._document_frequencies)
        if not known_terms:
            return ()
        scored: list[tuple[float, int]] = []
        for index in range(self._count):
            length = self._document_lengths[index]
            counts = self._token_counts[index]
            score = 0.0
            for term in known_terms:
                tf = counts.get(term, 0)
                if not tf:
                    continue
                df = self._document_frequencies[term]
                idf = math.log1p((self._count - df + 0.5) / (df + 0.5))
                normalization = 1.0 - self._config.b
                if self._average_document_length:
                    normalization += self._config.b * length / self._average_document_length
                denominator = tf + self._config.k1 * normalization
                score += idf * (tf * (self._config.k1 + 1.0)) / denominator
            if score > 0.0 and math.isfinite(score):
                scored.append((score, index))
        scored.sort(key=lambda item: (-item[0], item[1]))
        return tuple((index, score) for score, index in scored[:top_k])


class BM25Index:
    """An in-memory immutable BM25 index over Phase 1 ``RetrievalDocument`` values."""

    def __init__(self, documents: Sequence[RetrievalDocument] = (),
                 config: BM25Config | None = None) -> None:
        if config is not None and not isinstance(config, BM25Config):
            raise InvalidBM25ConfigError("config must be a BM25Config")
        self._config = config if config is not None else BM25Config()
        if not isinstance(documents, (tuple, list)):
            try:
                documents = tuple(documents)
            except TypeError as error:
                raise TypeError("documents must be an iterable of RetrievalDocument") from error
        corpus = tuple(documents)
        if not all(isinstance(document, RetrievalDocument) for document in corpus):
            raise TypeError("documents must contain RetrievalDocument values")
        canonical = tuple(sorted(corpus, key=lambda d: _symbol_id_key(d.symbol_id)))
        seen: set[SymbolId] = set()
        for document in canonical:
            if document.symbol_id in seen:
                raise DuplicateLexicalDocumentError(document.symbol_id)
            seen.add(document.symbol_id)
        self._documents = canonical
        self._scorer = BM25TextScorer(
            tuple(document.qualified_name + "\n" + document.source_text for document in canonical),
            self._config,
        )

    @property
    def config(self) -> BM25Config:
        return self._config

    @property
    def documents(self) -> tuple[RetrievalDocument, ...]:
        return self._documents

    @property
    def document_count(self) -> int:
        return len(self._documents)

    @property
    def average_document_length(self) -> float:
        return self._scorer.average_document_length

    @property
    def document_frequencies(self) -> Mapping[str, int]:
        return self._scorer.document_frequencies

    @property
    def document_lengths(self) -> tuple[int, ...]:
        return self._scorer.document_lengths

    def search(self, query: str, top_k: int = 10) -> tuple[LexicalHit, ...]:
        return tuple(
            LexicalHit(self._documents[index], score, rank)
            for rank, (index, score) in enumerate(self._scorer.search(query, top_k), start=1)
        )


BM25LexicalIndex = BM25Index
LexicalResult = LexicalHit
