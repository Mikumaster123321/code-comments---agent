from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Mapping

from code_maintenance.adapters import JavaAdapter, LanguageAdapter, PythonAdapter
from code_maintenance.domain import ProjectFile, SourceFile, Symbol, SymbolId
from code_maintenance.scanner import ProjectScanner
from code_maintenance.snapshot import FileState, ProjectSnapshot, SymbolState

from .domain import (
    CorpusBuildError,
    CorpusIOError,
    CorpusSnapshotMismatchError,
    DuplicateRetrievalDocumentError,
    RetrievalDocument,
)


def _symbol_id_key(symbol_id: SymbolId) -> tuple[str, str, str, str, str, int]:
    return (
        symbol_id.language,
        symbol_id.relative_path,
        symbol_id.qualified_name,
        symbol_id.kind.value,
        symbol_id.semantic_disambiguator or "",
        symbol_id.fallback_line if symbol_id.fallback_line is not None else -1,
    )


class CorpusBuilder:
    """Build an immutable symbol corpus aligned with one project snapshot."""

    def __init__(
        self,
        *,
        scanner: ProjectScanner | None = None,
        adapters: Mapping[str, LanguageAdapter] | None = None,
    ) -> None:
        self._scanner = scanner if scanner is not None else ProjectScanner()
        self._adapters = dict(
            adapters
            if adapters is not None
            else {"python": PythonAdapter(), "java": JavaAdapter()}
        )

    def build(
        self,
        project_root: str | Path,
        snapshot: ProjectSnapshot,
    ) -> tuple[RetrievalDocument, ...]:
        snapshot_files = self._snapshot_files(snapshot)
        snapshot_symbols = self._snapshot_symbols(snapshot, snapshot_files)
        first_scan = self._scan(project_root)
        self._validate_project(snapshot, first_scan.project.id)
        current_files = self._validate_files(snapshot_files, first_scan.files)

        source_by_path = {
            relative_path: self._read_source(
                Path(first_scan.project.root_path),
                state,
                current_files[relative_path],
            )
            for relative_path, state in sorted(snapshot_files.items())
            if state.language in self._adapters
        }

        documents = self._build_documents(
            snapshot.project_id,
            snapshot_files,
            snapshot_symbols,
            source_by_path,
        )

        final_scan = self._scan(project_root)
        self._validate_project(snapshot, final_scan.project.id)
        self._validate_files(snapshot_files, final_scan.files)
        return tuple(sorted(documents, key=lambda document: _symbol_id_key(document.symbol_id)))

    @staticmethod
    def _snapshot_files(snapshot: ProjectSnapshot) -> dict[str, FileState]:
        files: dict[str, FileState] = {}
        for state in snapshot.files:
            if state.relative_path in files:
                raise CorpusSnapshotMismatchError(
                    state.relative_path, "duplicate file state in snapshot"
                )
            files[state.relative_path] = state
        return files

    @staticmethod
    def _snapshot_symbols(
        snapshot: ProjectSnapshot,
        snapshot_files: Mapping[str, FileState],
    ) -> dict[str, dict[SymbolId, SymbolState]]:
        symbols: dict[str, dict[SymbolId, SymbolState]] = {
            relative_path: {} for relative_path in snapshot_files
        }
        seen: set[SymbolId] = set()
        for state in snapshot.symbols:
            relative_path = state.id.relative_path
            if relative_path not in snapshot_files:
                raise CorpusSnapshotMismatchError(
                    relative_path,
                    "symbol refers to a file absent from snapshot",
                    symbol_id=state.id,
                )
            if state.id in seen:
                raise DuplicateRetrievalDocumentError(state.id)
            seen.add(state.id)
            symbols[relative_path][state.id] = state
        return symbols

    def _scan(self, project_root: str | Path):
        try:
            return self._scanner.scan(project_root)
        except OSError as error:
            raise CorpusIOError("<project-root>", "scan", type(error).__name__) from error

    @staticmethod
    def _validate_project(snapshot: ProjectSnapshot, current_project_id: str) -> None:
        if current_project_id != snapshot.project_id:
            raise CorpusSnapshotMismatchError(
                "<project-root>", "project identity differs from snapshot"
            )

    @staticmethod
    def _validate_files(
        snapshot_files: Mapping[str, FileState],
        current_files: tuple[ProjectFile, ...],
    ) -> dict[str, ProjectFile]:
        current_by_path: dict[str, ProjectFile] = {}
        for project_file in current_files:
            if project_file.relative_path in current_by_path:
                raise CorpusSnapshotMismatchError(
                    project_file.relative_path, "duplicate file in current project scan"
                )
            current_by_path[project_file.relative_path] = project_file

        for relative_path, expected in sorted(snapshot_files.items()):
            current = current_by_path.get(relative_path)
            if current is None:
                raise CorpusSnapshotMismatchError(
                    relative_path, "snapshot file is missing from current project scan"
                )
            if current.language != expected.language:
                raise CorpusSnapshotMismatchError(
                    relative_path, "file language differs from snapshot"
                )
            if current.content_hash != expected.content_hash:
                raise CorpusSnapshotMismatchError(
                    relative_path, "file content hash differs from snapshot"
                )
        return current_by_path

    @staticmethod
    def _read_source(
        root: Path,
        expected: FileState,
        current: ProjectFile,
    ) -> str:
        candidate = root / current.relative_path
        try:
            if candidate.is_symlink():
                raise CorpusSnapshotMismatchError(
                    expected.relative_path, "snapshot path is not a regular source file"
                )
            resolved = candidate.resolve(strict=True)
            resolved.relative_to(root)
            if not resolved.is_file():
                raise CorpusSnapshotMismatchError(
                    expected.relative_path, "snapshot path is not a regular source file"
                )
            content = resolved.read_bytes()
        except CorpusSnapshotMismatchError:
            raise
        except (OSError, ValueError) as error:
            raise CorpusIOError(
                expected.relative_path, "read", type(error).__name__
            ) from error

        if sha256(content).hexdigest() != expected.content_hash:
            raise CorpusSnapshotMismatchError(
                expected.relative_path, "file changed while corpus was being built"
            )
        return content.decode("utf-8", errors="replace")

    def _build_documents(
        self,
        project_id: str,
        snapshot_files: Mapping[str, FileState],
        snapshot_symbols: Mapping[str, Mapping[SymbolId, SymbolState]],
        source_by_path: Mapping[str, str],
    ) -> list[RetrievalDocument]:
        documents: list[RetrievalDocument] = []
        seen: set[SymbolId] = set()
        for relative_path, expected_file in sorted(snapshot_files.items()):
            expected_symbols = snapshot_symbols[relative_path]
            adapter = self._adapters.get(expected_file.language)
            if adapter is None:
                if expected_symbols:
                    symbol_id = min(expected_symbols, key=_symbol_id_key)
                    raise CorpusSnapshotMismatchError(
                        relative_path,
                        "snapshot symbol has no supported language adapter",
                        symbol_id=symbol_id,
                    )
                continue

            source = source_by_path[relative_path]
            source_file = SourceFile(
                project_id=project_id,
                relative_path=relative_path,
                language=expected_file.language,
                content=source,
            )
            try:
                parsed_symbols = adapter.parse_symbols(source_file)
            except (SyntaxError, ValueError) as error:
                raise CorpusBuildError(
                    "corpus source parse failure: "
                    f"file='{relative_path}', error='{type(error).__name__}'"
                ) from error

            actual_by_id: dict[SymbolId, Symbol] = {}
            for symbol in parsed_symbols:
                if symbol.id in actual_by_id or symbol.id in seen:
                    raise DuplicateRetrievalDocumentError(symbol.id)
                actual_by_id[symbol.id] = symbol
                seen.add(symbol.id)

            expected_ids = set(expected_symbols)
            actual_ids = set(actual_by_id)
            missing = expected_ids - actual_ids
            if missing:
                symbol_id = min(missing, key=_symbol_id_key)
                raise CorpusSnapshotMismatchError(
                    relative_path,
                    "expected symbol is missing from current source",
                    symbol_id=symbol_id,
                )
            unexpected = actual_ids - expected_ids
            if unexpected:
                symbol_id = min(unexpected, key=_symbol_id_key)
                raise CorpusSnapshotMismatchError(
                    relative_path,
                    "current source contains a symbol absent from snapshot",
                    symbol_id=symbol_id,
                )

            for symbol_id in sorted(expected_ids, key=_symbol_id_key):
                symbol = actual_by_id[symbol_id]
                expected = expected_symbols[symbol_id]
                if symbol.content_hash != expected.content_hash:
                    raise CorpusSnapshotMismatchError(
                        relative_path,
                        "symbol content hash differs from snapshot",
                        symbol_id=symbol_id,
                    )
                documents.append(self._document(symbol, source))
        return documents

    @staticmethod
    def _document(symbol: Symbol, source: str) -> RetrievalDocument:
        lines = source.splitlines()
        if (
            type(symbol.start_line) is not int
            or type(symbol.end_line) is not int
            or symbol.start_line < 1
            or symbol.end_line < symbol.start_line
            or symbol.end_line > len(lines)
        ):
            raise CorpusSnapshotMismatchError(
                symbol.relative_path,
                "symbol source range is invalid",
                symbol_id=symbol.id,
            )
        source_text = "\n".join(lines[symbol.start_line - 1 : symbol.end_line])
        if sha256(source_text.encode("utf-8")).hexdigest() != symbol.content_hash:
            raise CorpusSnapshotMismatchError(
                symbol.relative_path,
                "symbol source range does not match its content hash",
                symbol_id=symbol.id,
            )
        return RetrievalDocument(
            symbol_id=symbol.id,
            language=symbol.language,
            relative_path=symbol.relative_path,
            qualified_name=symbol.qualified_name,
            kind=symbol.kind,
            signature=symbol.signature,
            source_text=source_text,
            documentation_text=None,
            content_hash=symbol.content_hash,
            start_line=symbol.start_line,
            end_line=symbol.end_line,
        )
