from __future__ import annotations

import re
from collections import Counter
from hashlib import sha256
from typing import Protocol

from Java.java_parser import get_defined_functions as get_java_functions
from Py.parser import get_defined_functions as get_python_functions

from .domain import SourceFile, Symbol, SymbolId, SymbolKind


class LanguageAdapter(Protocol):
    def parse_symbols(self, source_file: SourceFile) -> list[Symbol]: ...


def _content_hash(content: str) -> str:
    return sha256(content.encode("utf-8")).hexdigest()


def _containing_classes(items: list[dict], item: dict) -> list[dict]:
    parents = [
        candidate
        for candidate in items
        if candidate["type"] == "class"
        and candidate["lineno"] < item["lineno"]
        and candidate["end_lineno"] >= item["end_lineno"]
    ]
    return sorted(parents, key=lambda candidate: candidate["lineno"])


def _build_symbols(
    source_file: SourceFile,
    items: list[dict],
    language: str,
    signature_for,
) -> list[Symbol]:
    pending = []
    for item in items:
        parents = _containing_classes(items, item)
        qualified_name = ".".join([*(parent["name"] for parent in parents), item["name"]])
        kind = SymbolKind.CLASS if item["type"] == "class" else (
            SymbolKind.METHOD if parents else SymbolKind.FUNCTION
        )
        signature = signature_for(item) if kind != SymbolKind.CLASS else None
        disambiguator = signature if language == "java" and kind == SymbolKind.METHOD else None
        pending.append((item, kind, qualified_name, signature, disambiguator))

    base_keys = Counter(
        (kind, qualified_name, disambiguator)
        for _, kind, qualified_name, _, disambiguator in pending
    )
    symbols = []
    for item, kind, qualified_name, signature, disambiguator in pending:
        fallback_line = item["lineno"] if base_keys[(kind, qualified_name, disambiguator)] > 1 else None
        symbols.append(
            Symbol(
                id=SymbolId(
                    language=language,
                    relative_path=source_file.relative_path,
                    qualified_name=qualified_name,
                    kind=kind,
                    semantic_disambiguator=disambiguator,
                    fallback_line=fallback_line,
                ),
                name=item["name"],
                qualified_name=qualified_name,
                kind=kind,
                language=language,
                relative_path=source_file.relative_path,
                start_line=item["lineno"],
                end_line=item["end_lineno"],
                signature=signature,
                content_hash=_content_hash(item["code"]),
            )
        )
    return symbols


def _python_signature(item: dict) -> str:
    node = item["node"]
    arguments = [argument.arg for argument in node.args.posonlyargs + node.args.args]
    if node.args.vararg:
        arguments.append(f"*{node.args.vararg.arg}")
    arguments.extend(f"{argument.arg}" for argument in node.args.kwonlyargs)
    if node.args.kwarg:
        arguments.append(f"**{node.args.kwarg.arg}")
    return f"{item['name']}({', '.join(arguments)})"


def _java_signature(item: dict) -> str:
    match = re.search(rf"\b{re.escape(item['name'])}\s*\(([^)]*)\)", item["code"])
    if not match:
        return f"{item['name']}()"
    parameters = []
    for parameter in match.group(1).split(","):
        parameter = re.sub(r"\s+", " ", parameter.strip())
        if not parameter:
            continue
        parts = parameter.split(" ")
        parameters.append(" ".join(parts[:-1]) or parts[0])
    return f"{item['name']}({','.join(parameters)})"


class PythonAdapter:
    def parse_symbols(self, source_file: SourceFile) -> list[Symbol]:
        if source_file.language.lower() != "python":
            raise ValueError("PythonAdapter requires a Python SourceFile")
        return _build_symbols(source_file, get_python_functions(source_file.content), "python", _python_signature)


class JavaAdapter:
    def parse_symbols(self, source_file: SourceFile) -> list[Symbol]:
        if source_file.language.lower() != "java":
            raise ValueError("JavaAdapter requires a Java SourceFile")
        return _build_symbols(source_file, get_java_functions(source_file.content), "java", _java_signature)
