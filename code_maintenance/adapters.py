from __future__ import annotations

import re
from collections import Counter
from hashlib import sha256
from typing import Optional, Protocol

from Java.java_parser import get_defined_functions as get_java_functions
from Py.parser import get_defined_functions as get_python_functions

from .domain import SourceFile, Symbol, SymbolId, SymbolKind


class LanguageAdapter(Protocol):
    def parse_symbols(self, source_file: SourceFile) -> list[Symbol]: ...


def _content_hash(content: str) -> str:
    return sha256(content.encode("utf-8")).hexdigest()


def _contains(candidate: dict, item: dict) -> bool:
    candidate_node = candidate.get("node")
    item_node = item.get("node")
    if isinstance(candidate_node, dict) and isinstance(item_node, dict):
        candidate_open = candidate_node.get("brace_pos")
        candidate_close = candidate_node.get("close_pos")
        item_start = item_node.get("decl_start")
        item_close = item_node.get("close_pos")
        if all(isinstance(position, int) for position in (
            candidate_open,
            candidate_close,
            item_start,
            item_close,
        )) and candidate_close >= 0 and item_close >= 0:
            return candidate_open < item_start and candidate_close >= item_close
    return (
        candidate["lineno"] < item["lineno"]
        and candidate["end_lineno"] >= item["end_lineno"]
    )


def _containing_classes(items: list[dict], item: dict) -> list[dict]:
    parents = [
        candidate
        for candidate in items
        if candidate["type"] == "class"
        and _contains(candidate, item)
    ]
    def scope_start(candidate: dict) -> int:
        node = candidate.get("node")
        if isinstance(node, dict):
            return node.get("brace_pos", candidate["lineno"])
        return candidate["lineno"]

    return sorted(parents, key=lambda candidate: (scope_start(candidate), candidate["lineno"]))


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


def _split_java_parameters(parameters: str) -> list[str]:
    parts = []
    start = 0
    depths = {"<": 0, "[": 0, "(": 0}
    closing = {">": "<", "]": "[", ")": "("}
    for index, character in enumerate(parameters):
        if character in depths:
            depths[character] += 1
        elif character in closing:
            opener = closing[character]
            depths[opener] = max(0, depths[opener] - 1)
        elif character == "," and not any(depths.values()):
            parts.append(parameters[start:index])
            start = index + 1
    parts.append(parameters[start:])
    return parts


def _normalize_java_parameter(parameter: str) -> str:
    parameter = re.sub(r"\bfinal\b", "", parameter)
    parameter = re.sub(r"\s+", " ", parameter.strip())
    declaration = re.fullmatch(
        r"(.+?)\s+([A-Za-z_$][\w$]*)(\s*(?:\[\s*\]\s*)*)",
        parameter,
    )
    if declaration:
        parameter = declaration.group(1) + declaration.group(3)
    parameter = re.sub(r"\s*\.\s*\.\s*\.\s*", "...", parameter)
    parameter = re.sub(r"\s*([<>,\[\]])\s*", r"\1", parameter)
    return re.sub(r"\s+", " ", parameter.strip())


def _java_declaration(item: dict, source: str) -> str:
    node = item.get("node", {})
    start = node.get("decl_start")
    end = node.get("brace_pos")
    if isinstance(start, int) and isinstance(end, int):
        return source[start:end]
    return item["code"]


def _java_parameters(item: dict, source: str) -> Optional[str]:
    declaration = _java_declaration(item, source)
    match = re.search(rf"\b{re.escape(item['name'])}\s*\(", declaration)
    if not match:
        return None
    start = match.end()
    depth = 1
    for index in range(start, len(declaration)):
        if declaration[index] == "(":
            depth += 1
        elif declaration[index] == ")":
            depth -= 1
            if depth == 0:
                return declaration[start:index]
    return None


def _java_signature(item: dict, source: str) -> str:
    declaration = _java_parameters(item, source)
    if declaration is None:
        return f"{item['name']}()"
    parameters = [
        _normalize_java_parameter(parameter)
        for parameter in _split_java_parameters(declaration)
        if parameter.strip()
    ]
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
        return _build_symbols(
            source_file,
            get_java_functions(source_file.content),
            "java",
            lambda item: _java_signature(item, source_file.content),
        )
