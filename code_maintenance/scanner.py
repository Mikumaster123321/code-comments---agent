from __future__ import annotations

import fnmatch
import os
from collections import Counter
from hashlib import sha256
from pathlib import Path
from typing import Iterable, Union

from .domain import Project, ProjectDirectory, ProjectFile, ScanMetadata, ScanResult


DEFAULT_IGNORE_RULES = (
    ".git/",
    ".hg/",
    ".svn/",
    ".venv/",
    "venv/",
    "__pycache__/",
    ".pytest_cache/",
    ".mypy_cache/",
    ".ruff_cache/",
    "node_modules/",
    "*.pyc",
    ".DS_Store",
)

LANGUAGE_BY_SUFFIX = {
    ".c": "c",
    ".cc": "cpp",
    ".cpp": "cpp",
    ".cs": "csharp",
    ".css": "css",
    ".go": "go",
    ".h": "c",
    ".hpp": "cpp",
    ".html": "html",
    ".java": "java",
    ".js": "javascript",
    ".json": "json",
    ".jsx": "javascript",
    ".kt": "kotlin",
    ".md": "markdown",
    ".php": "php",
    ".py": "python",
    ".rb": "ruby",
    ".rs": "rust",
    ".sh": "shell",
    ".sql": "sql",
    ".swift": "swift",
    ".toml": "toml",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".xml": "xml",
    ".yaml": "yaml",
    ".yml": "yaml",
}


def _clean_rules(rules: Iterable[str]) -> tuple[str, ...]:
    cleaned = []
    for rule in rules:
        rule = rule.strip().replace("\\", "/")
        if rule and not rule.startswith("#"):
            cleaned.append(rule)
    return tuple(cleaned)


def _matches_rule(relative_path: str, is_directory: bool, rule: str) -> bool:
    negated = rule.startswith("!")
    if negated:
        rule = rule[1:]
    directory_only = rule.endswith("/")
    if directory_only and not is_directory:
        return False
    pattern = rule.rstrip("/")
    anchored = pattern.startswith("/")
    pattern = pattern.lstrip("/")
    if not pattern:
        return False
    if anchored:
        return fnmatch.fnmatchcase(relative_path, pattern)
    if "/" in pattern:
        return (
            fnmatch.fnmatchcase(relative_path, pattern)
            or fnmatch.fnmatchcase(relative_path, f"*/{pattern}")
        )
    return any(fnmatch.fnmatchcase(part, pattern) for part in relative_path.split("/"))


def _is_ignored(relative_path: str, is_directory: bool, rules: tuple[str, ...]) -> bool:
    ignored = False
    for rule in rules:
        if _matches_rule(relative_path, is_directory, rule):
            ignored = not rule.startswith("!")
    return ignored


def _hash_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _project_hash(
    directories: tuple[ProjectDirectory, ...],
    files: tuple[ProjectFile, ...],
) -> str:
    digest = sha256(b"project-scan-v1\0")
    for directory in directories:
        digest.update(b"directory\0")
        digest.update(directory.relative_path.encode("utf-8"))
        digest.update(b"\0")
    for file in files:
        digest.update(b"file\0")
        digest.update(file.relative_path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(file.language.encode("utf-8"))
        digest.update(b"\0")
        digest.update(file.content_hash.encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()


class ProjectScanner:
    """Discover project structure and metadata without performing code analysis."""

    def __init__(self, ignore_rules: Iterable[str] = ()) -> None:
        self._ignore_rules = _clean_rules(ignore_rules)

    def scan(self, root_path: Union[str, Path]) -> ScanResult:
        root = Path(root_path).expanduser().resolve(strict=True)
        if not root.is_dir():
            raise NotADirectoryError(str(root))

        gitignore = root / ".gitignore"
        repository_rules = ()
        if gitignore.is_file():
            repository_rules = _clean_rules(
                gitignore.read_text(encoding="utf-8", errors="replace").splitlines()
            )
        ignore_rules = DEFAULT_IGNORE_RULES + repository_rules + self._ignore_rules

        directories = [ProjectDirectory(".")]
        files = []
        skipped_entries = 0

        def on_error(_error: OSError) -> None:
            nonlocal skipped_entries
            skipped_entries += 1

        for current_path, directory_names, file_names in os.walk(
            root, topdown=True, followlinks=False, onerror=on_error
        ):
            current = Path(current_path)
            kept_directories = []
            for name in sorted(directory_names):
                path = current / name
                relative_path = path.relative_to(root).as_posix()
                if path.is_symlink() or _is_ignored(relative_path, True, ignore_rules):
                    continue
                kept_directories.append(name)
                directories.append(ProjectDirectory(relative_path))
            directory_names[:] = kept_directories

            for name in sorted(file_names):
                path = current / name
                relative_path = path.relative_to(root).as_posix()
                if path.is_symlink() or _is_ignored(relative_path, False, ignore_rules):
                    continue
                try:
                    stat = path.stat()
                    if not path.is_file():
                        continue
                    files.append(
                        ProjectFile(
                            relative_path=relative_path,
                            language=LANGUAGE_BY_SUFFIX.get(path.suffix.lower(), "unknown"),
                            size_bytes=stat.st_size,
                            modified_time_ns=stat.st_mtime_ns,
                            content_hash=_hash_file(path),
                        )
                    )
                except OSError:
                    skipped_entries += 1

        sorted_directories = tuple(
            sorted(directories, key=lambda item: item.relative_path)
        )
        sorted_files = tuple(sorted(files, key=lambda item: item.relative_path))
        language_counts = tuple(
            sorted(Counter(file.language for file in sorted_files).items())
        )
        metadata = ScanMetadata(
            directory_count=len(sorted_directories),
            file_count=len(sorted_files),
            total_bytes=sum(file.size_bytes for file in sorted_files),
            language_counts=language_counts,
            skipped_entries=skipped_entries,
        )
        resolved_root = str(root)
        project = Project(
            id=sha256(resolved_root.encode("utf-8")).hexdigest(),
            name=root.name,
            root_path=resolved_root,
        )
        return ScanResult(
            project=project,
            directories=sorted_directories,
            files=sorted_files,
            ignore_rules=ignore_rules,
            metadata=metadata,
            content_hash=_project_hash(sorted_directories, sorted_files),
        )
