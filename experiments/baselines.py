from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Sequence

from code_maintenance import SymbolId
from project_intelligence import BM25Config, tokenize

from .config import ChunkExperimentConfig, FileExperimentConfig, RetrievalUnit
from .reference import ReferenceRecord
from .schemas import DatasetManifest, GroundTruthRecord, SchemaValidationError, symbol_identity
from .serialization import normalize_lf, normalize_relative_path, sha256_hex


class BaselineValidationError(ValueError):
    pass


@dataclass(frozen=True, order=True)
class FileIdentity:
    relative_path: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "relative_path", normalize_relative_path(self.relative_path))

    def serialize(self) -> str:
        return f"file:{self.relative_path}"


@dataclass(frozen=True, order=True)
class ChunkIdentity:
    relative_path: str
    start_offset: int
    end_offset: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "relative_path", normalize_relative_path(self.relative_path))
        if (
            type(self.start_offset) is not int
            or type(self.end_offset) is not int
            or self.start_offset < 0
            or self.end_offset <= self.start_offset
        ):
            raise BaselineValidationError("chunk identity requires a non-empty valid span")

    def serialize(self) -> str:
        return f"chunk:{self.relative_path}:{self.start_offset}:{self.end_offset}"


CandidateIdentity = FileIdentity | ChunkIdentity | SymbolId


def serialize_candidate_identity(identity: CandidateIdentity) -> str:
    if isinstance(identity, (FileIdentity, ChunkIdentity)):
        return identity.serialize()
    if isinstance(identity, SymbolId):
        return symbol_identity(identity)
    raise BaselineValidationError("unsupported candidate identity")


@dataclass(frozen=True)
class FileSource:
    relative_path: str
    source: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "relative_path", normalize_relative_path(self.relative_path))
        object.__setattr__(self, "source", normalize_lf(self.source))


@dataclass(frozen=True)
class BaselineDocument:
    identity: FileIdentity | ChunkIdentity
    relative_path: str
    text: str
    source_text: str
    start_offset: int | None
    end_offset: int | None

    def __post_init__(self) -> None:
        object.__setattr__(self, "relative_path", normalize_relative_path(self.relative_path))
        if self.identity.relative_path != self.relative_path:
            raise BaselineValidationError("document path must match identity")
        if not isinstance(self.text, str) or not isinstance(self.source_text, str):
            raise BaselineValidationError("document text must be strings")


def build_file_documents(
    sources: Iterable[FileSource], config: FileExperimentConfig = FileExperimentConfig()
) -> tuple[BaselineDocument, ...]:
    if not isinstance(config, FileExperimentConfig):
        raise BaselineValidationError("config must be FileExperimentConfig")
    files = tuple(sources)
    if not all(isinstance(item, FileSource) for item in files):
        raise BaselineValidationError("sources must contain FileSource values")
    canonical = tuple(sorted(files, key=lambda item: item.relative_path))
    if len({item.relative_path for item in canonical}) != len(canonical):
        raise BaselineValidationError("source paths must be unique")
    return tuple(
        BaselineDocument(
            identity=FileIdentity(item.relative_path),
            relative_path=item.relative_path,
            text=item.relative_path + "\n" + item.source,
            source_text=item.source,
            start_offset=None,
            end_offset=None,
        )
        for item in canonical
    )


def build_chunk_documents(
    sources: Iterable[FileSource], config: ChunkExperimentConfig = ChunkExperimentConfig()
) -> tuple[BaselineDocument, ...]:
    if not isinstance(config, ChunkExperimentConfig):
        raise BaselineValidationError("config must be ChunkExperimentConfig")
    files = tuple(sources)
    if not all(isinstance(item, FileSource) for item in files):
        raise BaselineValidationError("sources must contain FileSource values")
    canonical = tuple(sorted(files, key=lambda item: item.relative_path))
    if len({item.relative_path for item in canonical}) != len(canonical):
        raise BaselineValidationError("source paths must be unique")
    documents: list[BaselineDocument] = []
    for item in canonical:
        for start in range(0, len(item.source), config.stride):
            end = min(start + config.size, len(item.source))
            chunk_text = item.source[start:end]
            if not chunk_text:
                continue
            identity = ChunkIdentity(item.relative_path, start, end)
            documents.append(
                BaselineDocument(
                    identity=identity,
                    relative_path=item.relative_path,
                    text=item.relative_path + "\n" + chunk_text,
                    source_text=chunk_text,
                    start_offset=start,
                    end_offset=end,
                )
            )
    return tuple(documents)


@dataclass(frozen=True)
class BaselineHit:
    identity: FileIdentity | ChunkIdentity
    relative_path: str
    rank: int
    score: float


class ExperimentalBM25Index:
    """Experiment-only BM25 over frozen File or Chunk text representations."""

    def __init__(
        self,
        documents: Sequence[BaselineDocument],
        config: BM25Config = BM25Config(),
    ) -> None:
        if not isinstance(config, BM25Config):
            raise BaselineValidationError("config must be BM25Config")
        values = tuple(documents)
        if not all(isinstance(item, BaselineDocument) for item in values):
            raise BaselineValidationError("documents must contain BaselineDocument values")
        self._documents = tuple(
            sorted(values, key=lambda item: serialize_candidate_identity(item.identity))
        )
        identities = [item.identity for item in self._documents]
        if len(identities) != len(set(identities)):
            raise BaselineValidationError("baseline document identities must be unique")
        self._config = config
        counts: list[dict[str, int]] = []
        lengths: list[int] = []
        frequencies: dict[str, int] = {}
        for document in self._documents:
            tokens = tokenize(document.text)
            current: dict[str, int] = {}
            for token in tokens:
                current[token] = current.get(token, 0) + 1
            counts.append(current)
            lengths.append(len(tokens))
            for token in current:
                frequencies[token] = frequencies.get(token, 0) + 1
        self._counts = tuple(counts)
        self._lengths = tuple(lengths)
        self._frequencies = frequencies
        self._average_length = sum(lengths) / len(lengths) if lengths else 0.0

    @property
    def documents(self) -> tuple[BaselineDocument, ...]:
        return self._documents

    @property
    def candidate_identities(self) -> tuple[FileIdentity | ChunkIdentity, ...]:
        return tuple(item.identity for item in self._documents)

    def search(self, query: str, top_k: int = 10) -> tuple[BaselineHit, ...]:
        if not isinstance(query, str):
            raise BaselineValidationError("query must be a string")
        if type(top_k) is not int or top_k <= 0:
            raise BaselineValidationError("top_k must be a positive integer")
        if not query.strip() or not self._documents or self._average_length == 0:
            return ()
        terms = tuple(dict.fromkeys(tokenize(query)))
        known = tuple(term for term in terms if term in self._frequencies)
        if not known:
            return ()
        scored: list[tuple[float, BaselineDocument]] = []
        total = len(self._documents)
        for index, document in enumerate(self._documents):
            score = 0.0
            for term in known:
                frequency = self._counts[index].get(term, 0)
                if not frequency:
                    continue
                document_frequency = self._frequencies[term]
                inverse = math.log1p(
                    (total - document_frequency + 0.5) / (document_frequency + 0.5)
                )
                normalization = 1 - self._config.b + (
                    self._config.b * self._lengths[index] / self._average_length
                )
                denominator = frequency + self._config.k1 * normalization
                score += inverse * (
                    frequency * (self._config.k1 + 1) / denominator
                )
            if score > 0 and math.isfinite(score):
                scored.append((score, document))
        scored.sort(
            key=lambda item: (-item[0], serialize_candidate_identity(item[1].identity))
        )
        return tuple(
            BaselineHit(document.identity, document.relative_path, rank, score)
            for rank, (score, document) in enumerate(scored[:top_k], start=1)
        )


@dataclass(frozen=True)
class SymbolSourceRange:
    symbol_id: SymbolId
    start_offset: int
    end_offset: int

    def __post_init__(self) -> None:
        if not isinstance(self.symbol_id, SymbolId):
            raise SchemaValidationError("symbol range requires a SymbolId")
        if (
            type(self.start_offset) is not int
            or type(self.end_offset) is not int
            or self.start_offset < 0
            or self.end_offset <= self.start_offset
        ):
            raise SchemaValidationError("symbol range requires a non-empty source span")


@dataclass(frozen=True)
class RuntimeDatasetFile:
    project_id: str
    relative_path: str
    source_text: str
    content_hash: str

    def __post_init__(self) -> None:
        if not isinstance(self.project_id, str) or not self.project_id:
            raise SchemaValidationError("runtime file project_id must be non-empty")
        object.__setattr__(self, "relative_path", normalize_relative_path(self.relative_path))
        object.__setattr__(self, "source_text", normalize_lf(self.source_text))
        if self.content_hash != sha256_hex(self.source_text):
            raise SchemaValidationError("runtime file content hash does not match source evidence")


@dataclass(frozen=True)
class AuthoritativeCandidate:
    project_id: str
    retrieval_unit: RetrievalUnit
    identity: CandidateIdentity
    content_hash: str
    start_offset: int | None = None
    end_offset: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.project_id, str) or not self.project_id:
            raise SchemaValidationError("candidate project_id must be non-empty")
        if not isinstance(self.retrieval_unit, RetrievalUnit):
            raise SchemaValidationError("candidate retrieval_unit is invalid")
        serialize_candidate_identity(self.identity)
        expected_type = {
            RetrievalUnit.FILE: FileIdentity,
            RetrievalUnit.CHUNK: ChunkIdentity,
            RetrievalUnit.SYMBOL: SymbolId,
        }[self.retrieval_unit]
        if not isinstance(self.identity, expected_type):
            raise SchemaValidationError("candidate identity does not match retrieval unit")
        if len(self.content_hash) != 64 or any(c not in "0123456789abcdef" for c in self.content_hash):
            raise SchemaValidationError("candidate content_hash must be SHA-256")
        if self.retrieval_unit is RetrievalUnit.SYMBOL:
            if (
                type(self.start_offset) is not int
                or type(self.end_offset) is not int
                or self.start_offset < 0
                or self.end_offset <= self.start_offset
            ):
                raise SchemaValidationError("symbol candidate requires an authoritative source range")
        elif self.start_offset is not None or self.end_offset is not None:
            raise SchemaValidationError("only symbol candidates carry separate source ranges")

    @property
    def relative_path(self) -> str:
        return self.identity.relative_path


class DatasetEvidenceRegistry:
    """Validated, frozen candidate universe; retrievers cannot define metric truth."""

    def __init__(
        self,
        manifest: DatasetManifest,
        files: Iterable[RuntimeDatasetFile],
        candidates: Iterable[AuthoritativeCandidate],
    ) -> None:
        if not isinstance(manifest, DatasetManifest):
            raise SchemaValidationError("registry requires a DatasetManifest")
        file_values = tuple(files)
        candidate_values = tuple(candidates)
        manifest_files = {
            (project.project_id, item.relative_path): item.content_hash
            for project in manifest.projects
            for item in project.files
        }
        runtime_files = {(item.project_id, item.relative_path): item for item in file_values}
        if len(runtime_files) != len(file_values):
            raise SchemaValidationError("runtime dataset file identities must be unique")
        if set(runtime_files) != set(manifest_files):
            raise SchemaValidationError("runtime dataset path set does not match manifest")
        for key, item in runtime_files.items():
            if item.content_hash != manifest_files[key]:
                raise SchemaValidationError("runtime dataset file hash does not match manifest")
        keys: set[tuple[str, RetrievalUnit, str]] = set()
        for item in candidate_values:
            if not isinstance(item, AuthoritativeCandidate):
                raise SchemaValidationError("registry candidates are invalid")
            file_item = runtime_files.get((item.project_id, item.relative_path))
            if file_item is None or file_item.content_hash != item.content_hash:
                raise SchemaValidationError("candidate is not backed by manifest source evidence")
            if isinstance(item.identity, ChunkIdentity) and item.identity.end_offset > len(file_item.source_text):
                raise SchemaValidationError("chunk candidate exceeds frozen source")
            if item.retrieval_unit is RetrievalUnit.SYMBOL and item.end_offset > len(file_item.source_text):
                raise SchemaValidationError("symbol candidate exceeds frozen source")
            key = (item.project_id, item.retrieval_unit, serialize_candidate_identity(item.identity))
            if key in keys:
                raise SchemaValidationError("authoritative candidate IDs must be unique")
            keys.add(key)
        for project in manifest.projects:
            project_candidates = tuple(
                item for item in candidate_values if item.project_id == project.project_id
            )
            expected_files = {item.relative_path for item in project.files}
            candidate_files = {
                item.relative_path for item in project_candidates
                if item.retrieval_unit is RetrievalUnit.FILE
            }
            if candidate_files != expected_files:
                raise SchemaValidationError("file candidate population must exactly match manifest")
            symbol_candidates = tuple(
                item for item in project_candidates
                if item.retrieval_unit is RetrievalUnit.SYMBOL
            )
            if len(symbol_candidates) != project.symbol_count:
                raise SchemaValidationError("symbol candidate population must match manifest count")
            expected_chunks = {
                document.identity
                for document in build_chunk_documents(
                    _runtime_file_source(runtime_files[(project.project_id, item.relative_path)])
                    for item in project.files
                )
            }
            candidate_chunks = {
                item.identity for item in project_candidates
                if item.retrieval_unit is RetrievalUnit.CHUNK
            }
            if candidate_chunks != expected_chunks:
                raise SchemaValidationError("chunk candidate population must match frozen construction")
        self.manifest = manifest
        self._files = runtime_files
        self._candidates = tuple(sorted(candidate_values, key=lambda item: (
            item.project_id, item.retrieval_unit.value, serialize_candidate_identity(item.identity)
        )))

    def candidates_for(self, project_id: str, unit: RetrievalUnit) -> tuple[CandidateIdentity, ...]:
        result = tuple(
            item.identity for item in self._candidates
            if item.project_id == project_id and item.retrieval_unit is unit
        )
        if not result:
            raise SchemaValidationError("authoritative candidate population is empty")
        return result

    def symbol_ranges_for(self, project_id: str) -> tuple[SymbolSourceRange, ...]:
        return tuple(
            SymbolSourceRange(item.identity, item.start_offset, item.end_offset)
            for item in self._candidates
            if item.project_id == project_id and item.retrieval_unit is RetrievalUnit.SYMBOL
        )

    def validate_truth(self, truth: GroundTruthRecord | ReferenceRecord) -> None:
        symbol_ids = {
            item.identity for item in self._candidates
            if item.project_id == truth.project_id and item.retrieval_unit is RetrievalUnit.SYMBOL
        }
        for evidence in truth.evidence:
            if (truth.project_id, evidence.relative_path) not in self._files:
                raise SchemaValidationError("ground-truth path is outside the manifest")
            if evidence.symbol_id is not None and evidence.symbol_id not in symbol_ids:
                raise SchemaValidationError("ground-truth SymbolId is outside authoritative evidence")
            source = self._files[(truth.project_id, evidence.relative_path)].source_text
            if evidence.end_offset is not None and evidence.end_offset > len(source):
                raise SchemaValidationError("ground-truth span exceeds frozen source")

    def validate_retrieved(
        self,
        project_id: str,
        unit: RetrievalUnit,
        identity: CandidateIdentity,
        relative_path: str,
        symbol_id: SymbolId | None,
        start_offset: int | None,
        end_offset: int | None,
    ) -> None:
        serialized = serialize_candidate_identity(identity)
        candidates = {
            serialize_candidate_identity(item.identity): item
            for item in self._candidates
            if item.project_id == project_id and item.retrieval_unit is unit
        }
        authoritative = candidates.get(serialized)
        if authoritative is None:
            raise SchemaValidationError("retrieved candidate is outside authoritative dataset evidence")
        if normalize_relative_path(relative_path) != authoritative.relative_path:
            raise SchemaValidationError("retrieved candidate path does not match authoritative identity")
        if unit is RetrievalUnit.SYMBOL and symbol_id != identity:
            raise SchemaValidationError("retrieved SymbolId does not match authoritative identity")
        expected_span = (
            (authoritative.start_offset, authoritative.end_offset)
            if unit is RetrievalUnit.SYMBOL else
            (identity.start_offset, identity.end_offset) if unit is RetrievalUnit.CHUNK else
            (None, None)
        )
        if (start_offset, end_offset) != expected_span:
            raise SchemaValidationError("retrieved source span does not match authoritative evidence")


def _runtime_file_source(item: RuntimeDatasetFile) -> FileSource:
    return FileSource(item.relative_path, item.source_text)


class TruthMapper:
    def __init__(
        self,
        truth: GroundTruthRecord | ReferenceRecord,
        symbol_ranges: Iterable[SymbolSourceRange] = (),
    ) -> None:
        if not isinstance(truth, (GroundTruthRecord, ReferenceRecord)):
            raise SchemaValidationError("truth must be a GroundTruthRecord or ReferenceRecord")
        ranges = tuple(symbol_ranges)
        if not all(isinstance(item, SymbolSourceRange) for item in ranges):
            raise SchemaValidationError("symbol_ranges must contain SymbolSourceRange values")
        if len({item.symbol_id for item in ranges}) != len(ranges):
            raise SchemaValidationError("symbol ranges must have unique SymbolId values")
        self._truth = truth
        self._ranges = {item.symbol_id: item for item in ranges}

    def _evidence_span(self, evidence) -> tuple[int, int] | None:
        if evidence.start_offset is not None:
            return evidence.start_offset, evidence.end_offset
        if evidence.symbol_id is not None:
            symbol_range = self._ranges.get(evidence.symbol_id)
            if symbol_range is None:
                return None
            return symbol_range.start_offset, symbol_range.end_offset
        return None

    def grade(self, identity: CandidateIdentity) -> int:
        grades: list[int] = []
        if isinstance(identity, FileIdentity):
            grades = [
                evidence.relevance
                for evidence in self._truth.evidence
                if evidence.relative_path == identity.relative_path
            ]
        elif isinstance(identity, SymbolId):
            symbol_range = self._ranges.get(identity)
            for evidence in self._truth.evidence:
                if evidence.symbol_id == identity:
                    grades.append(evidence.relevance)
                    continue
                if symbol_range is None or evidence.relative_path != identity.relative_path:
                    continue
                span = self._evidence_span(evidence)
                if span is not None and (
                    symbol_range.start_offset <= span[0]
                    and span[1] <= symbol_range.end_offset
                ):
                    grades.append(evidence.relevance)
        elif isinstance(identity, ChunkIdentity):
            for evidence in self._truth.evidence:
                if evidence.relative_path != identity.relative_path:
                    continue
                span = self._evidence_span(evidence)
                if span is None:
                    if evidence.relevance > 0:
                        raise SchemaValidationError(
                            "symbol-only evidence requires a frozen Symbol source range for Chunk mapping"
                        )
                    continue
                if max(identity.start_offset, span[0]) < min(identity.end_offset, span[1]):
                    grades.append(evidence.relevance)
        else:
            raise SchemaValidationError("unsupported candidate identity")
        return max(grades, default=0)

    def relevance_map(
        self, candidates: Iterable[CandidateIdentity]
    ) -> dict[str, int]:
        mapped: dict[str, int] = {}
        for identity in candidates:
            key = serialize_candidate_identity(identity)
            if key in mapped:
                raise SchemaValidationError("candidate identities must be unique")
            mapped[key] = self.grade(identity)
        if not any(grade > 0 for grade in mapped.values()):
            raise SchemaValidationError(
                "active retrieval unit has no mapped grade-1-or-2 truth"
            )
        return mapped
