from __future__ import annotations

import json
import math
import os
import re
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from enum import Enum
from hashlib import sha256
from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import Any, Iterable


class SerializationError(ValueError):
    """Raised when an experiment artifact is unsafe or non-canonical."""


_CREDENTIAL_KEY = re.compile(
    r"(?:credential|password|passwd|secret|api[_-]?key|access[_-]?token|auth[_-]?token)",
    re.IGNORECASE,
)
_CREDENTIAL_VALUE = re.compile(
    r"(?:sk-(?:proj-)?[A-Za-z0-9_-]{12,}|Bearer\s+[A-Za-z0-9._~+/=-]{12,}|"
    r"AKIA[A-Z0-9]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----|"
    r"SECRET_MARKER|SOURCE_MARKER)",
    re.IGNORECASE,
)


def normalize_relative_path(value: str) -> str:
    if not isinstance(value, str) or not value:
        raise SerializationError("relative path must be a non-empty string")
    normalized = value.replace("\\", "/")
    path = PurePosixPath(normalized)
    if path.is_absolute() or normalized.startswith("~/"):
        raise SerializationError("absolute paths are forbidden in experiment identity")
    if any(part in ("", ".", "..") for part in path.parts):
        raise SerializationError("relative path must be normalized and traversal-free")
    return path.as_posix()


def normalize_lf(value: str) -> str:
    if not isinstance(value, str):
        raise SerializationError("source must be a string")
    return value.replace("\r\n", "\n").replace("\r", "\n")


def _plain(value: Any) -> Any:
    if hasattr(value, "to_record"):
        return _plain(value.to_record())
    if is_dataclass(value):
        return _plain({field.name: getattr(value, field.name) for field in fields(value)})
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(item) for item in value]
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise SerializationError("non-finite numbers are forbidden")
        return value
    raise SerializationError(f"unsupported artifact value: {type(value).__name__}")


def _validate_private_data(value: Any, path: tuple[str, ...] = ()) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if _CREDENTIAL_KEY.search(str(key)):
                raise SerializationError(
                    f"credential-bearing field is forbidden: {'.'.join((*path, str(key)))}"
                )
            _validate_private_data(item, (*path, str(key)))
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_private_data(item, (*path, str(index)))
        return
    if isinstance(value, str) and _CREDENTIAL_VALUE.search(value):
        raise SerializationError("credential-like artifact value is forbidden")


def canonical_json(value: Any, *, pretty: bool = False) -> str:
    plain = _plain(value)
    _validate_private_data(plain)
    if pretty:
        return json.dumps(plain, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    return json.dumps(
        plain, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def canonical_json_bytes(value: Any) -> bytes:
    return canonical_json(value).encode("utf-8")


def canonical_hash(value: Any) -> str:
    return sha256(canonical_json_bytes(value)).hexdigest()


def canonical_jsonl(records: Iterable[Any]) -> str:
    return "".join(canonical_json(record) + "\n" for record in records)


def immutable_mapping(value: Mapping[str, Any]) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise SerializationError("value must be a mapping")
    frozen: dict[str, Any] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise SerializationError("mapping keys must be strings")
        if isinstance(item, Mapping):
            frozen[key] = immutable_mapping(item)
        elif isinstance(item, list):
            frozen[key] = tuple(item)
        else:
            frozen[key] = item
    return MappingProxyType(frozen)


def sha256_hex(content: bytes | str) -> str:
    payload = content.encode("utf-8") if isinstance(content, str) else content
    return sha256(payload).hexdigest()


def is_absolute_host_path(value: str) -> bool:
    return os.path.isabs(value) or bool(re.match(r"^[A-Za-z]:[\\/]", value))
