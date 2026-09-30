from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from code_maintenance.domain import SymbolId, SymbolKind


class ProjectIntelligenceError(Exception):
    """Base error for the project-intelligence boundary."""


class CorpusBuildError(ProjectIntelligenceError):
    """Raised when a complete authoritative corpus cannot be built."""


class CorpusSnapshotMismatchError(CorpusBuildError):
    def __init__(
        self,
        relative_path: str,
        reason: str,
        *,
        symbol_id: SymbolId | None = None,
    ) -> None:
        location = f"file='{relative_path}'"
        if symbol_id is not None:
            location += f", symbol='{symbol_id}'"
        super().__init__(f"corpus snapshot mismatch: {location}; reason='{reason}'")


class DuplicateRetrievalDocumentError(CorpusBuildError):
    def __init__(self, symbol_id: SymbolId) -> None:
        super().__init__(f"duplicate retrieval symbol: symbol='{symbol_id}'")


class CorpusIOError(CorpusBuildError):
    def __init__(self, relative_path: str, operation: str, error_type: str) -> None:
        super().__init__(
            "corpus source I/O failure: "
            f"file='{relative_path}', operation='{operation}', error='{error_type}'"
        )


@dataclass(frozen=True)
class RetrievalDocument:
    symbol_id: SymbolId
    language: str
    relative_path: str
    qualified_name: str
    kind: SymbolKind
    signature: Optional[str]
    source_text: str
    documentation_text: Optional[str]
    content_hash: str
    start_line: int
    end_line: int

    def __post_init__(self) -> None:
        identity_fields = (
            ("language", self.language, self.symbol_id.language),
            ("relative_path", self.relative_path, self.symbol_id.relative_path),
            ("qualified_name", self.qualified_name, self.symbol_id.qualified_name),
            ("kind", self.kind, self.symbol_id.kind),
        )
        for field_name, value, identity_value in identity_fields:
            if value != identity_value:
                raise ValueError(f"{field_name} must match symbol_id")
        if type(self.start_line) is not int or self.start_line < 1:
            raise ValueError("start_line must be a positive integer")
        if type(self.end_line) is not int or self.end_line < self.start_line:
            raise ValueError("end_line must be an integer at or after start_line")
