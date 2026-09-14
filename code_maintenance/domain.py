from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from hashlib import sha256
from typing import Optional


def _normalize_relative_path(relative_path: str) -> str:
    return relative_path.replace("\\", "/")


class SymbolKind(str, Enum):
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"


@dataclass(frozen=True)
class Project:
    id: str
    name: str
    root_path: str


@dataclass(frozen=True)
class ProjectDirectory:
    relative_path: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "relative_path", _normalize_relative_path(self.relative_path))


@dataclass(frozen=True)
class ProjectFile:
    relative_path: str
    language: str
    size_bytes: int
    modified_time_ns: int
    content_hash: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "relative_path", _normalize_relative_path(self.relative_path))


@dataclass(frozen=True)
class ScanMetadata:
    directory_count: int
    file_count: int
    total_bytes: int
    language_counts: tuple[tuple[str, int], ...]
    skipped_entries: int = 0


@dataclass(frozen=True)
class ScanResult:
    project: Project
    directories: tuple[ProjectDirectory, ...]
    files: tuple[ProjectFile, ...]
    ignore_rules: tuple[str, ...]
    metadata: ScanMetadata
    content_hash: str


@dataclass(frozen=True)
class SourceFile:
    project_id: str
    relative_path: str
    language: str
    content: str
    content_hash: str = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "relative_path", _normalize_relative_path(self.relative_path))
        object.__setattr__(self, "content_hash", sha256(self.content.encode("utf-8")).hexdigest())


@dataclass(frozen=True)
class SymbolId:
    language: str
    relative_path: str
    qualified_name: str
    kind: SymbolKind
    semantic_disambiguator: Optional[str] = None
    fallback_line: Optional[int] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "relative_path", _normalize_relative_path(self.relative_path))

    def __str__(self) -> str:
        parts = [self.language, self.relative_path, self.qualified_name, self.kind.value]
        if self.semantic_disambiguator:
            parts.append(self.semantic_disambiguator)
        if self.fallback_line is not None:
            parts.append(f"line:{self.fallback_line}")
        return ":".join(parts)


@dataclass(frozen=True)
class Symbol:
    id: SymbolId
    name: str
    qualified_name: str
    kind: SymbolKind
    language: str
    relative_path: str
    start_line: int
    end_line: int
    signature: Optional[str]
    content_hash: str


@dataclass(frozen=True)
class AnalysisFinding:
    rule_id: str
    message: str
    severity: str
    relative_path: str
    line: int
    symbol_id: Optional[SymbolId] = None
