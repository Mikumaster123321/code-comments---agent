# -*- coding: utf-8 -*-
"""Workspace persistence implementation extracted from the root processor module."""

from __future__ import annotations

import datetime
import os
import tempfile
from typing import Optional

# ================== v2.3.7 工作区保存 / 恢复（会话持久化）==================
"""
持久化策略：双存储，容错优先
  1) 主存储：服务端 tempfile.gettempdir() / "<user_hash>_code_comments_agent_workspace.json"
     —— Linux/Mac/Windows 都有稳定 temp 目录，多用户靠 user_hash 避免冲突
  2) 辅助：ui 层 JS 桥写 localStorage（后端不可用时兜底）
"""
import json as _json
import getpass as _getpass
import hashlib as _hashlib

_WS_FILENAME = "code_comments_agent_workspace.json"
_WS_VERSION = 1

# 白名单：只允许这些字段持久化，绝不写 API Key
WS_ALLOWED_FIELDS = frozenset({
    "source_code", "language", "ui_lang", "output_lang",
    "python_style", "java_style", "rewrite_existing", "naming_strategy",
})


def _default_workspace_path() -> str:
    try:
        user = _getpass.getuser() or "default"
    except Exception:
        user = "default"
    user_hash = _hashlib.md5(user.encode("utf-8")).hexdigest()[:8]
    return os.path.join(tempfile.gettempdir(), f"{user_hash}_{_WS_FILENAME}")


def save_workspace(data: dict, path: Optional[str] = None) -> tuple[bool, str]:
    path = path or _default_workspace_path()
    tmp_out = path + ".tmp"
    try:
        filtered = {k: v for k, v in (data or {}).items()
                    if k in WS_ALLOWED_FIELDS and v is not None}
        payload = {
            "_version": _WS_VERSION,
            "_saved_at": datetime.datetime.now().isoformat(timespec="seconds"),
            "data": filtered,
        }
        with open(tmp_out, "w", encoding="utf-8") as f:
            _json.dump(payload, f, ensure_ascii=False, indent=2)
        os.replace(tmp_out, path)  # 原子替换
        return True, f"✅ 会话已保存（{len(filtered)} 项 → {os.path.basename(path)}）"
    except Exception:
        try:
            os.remove(tmp_out)
        except OSError:
            pass
        return False, "❌ [WORKSPACE_SAVE_FAILED] 工作区保存失败，请重试。"


def load_workspace(path: Optional[str] = None) -> tuple[bool, str, dict]:
    path = path or _default_workspace_path()
    try:
        if not os.path.isfile(path):
            return False, "ℹ️ 未找到上次保存的会话", {}
        with open(path, "r", encoding="utf-8") as f:
            payload = _json.load(f)
        if not isinstance(payload, dict) or not isinstance(payload.get("data"), dict):
            return False, "❌ 会话文件格式异常", {}
        version = payload.get("_version")
        if version != _WS_VERSION:
            return False, "❌ [WORKSPACE_VERSION_UNSUPPORTED] 会话版本不受支持，请重新保存。", {}
        data = payload["data"]
        filtered = {k: v for k, v in data.items() if k in WS_ALLOWED_FIELDS}
        saved_at = payload.get("_saved_at", "?")
        return True, f"✅ 会话已恢复（{len(filtered)} 项，保存于 {saved_at}）", filtered
    except UnicodeDecodeError:
        return False, "❌ 会话文件编码错误", {}
    except _json.JSONDecodeError:
        return False, "❌ 会话文件已损坏（JSON 解析失败）", {}
    except Exception:
        return False, "❌ [WORKSPACE_RESTORE_FAILED] 工作区恢复失败，请重新保存。", {}


def clear_workspace(path: Optional[str] = None) -> tuple[bool, str]:
    path = path or _default_workspace_path()
    try:
        if os.path.isfile(path):
            os.remove(path)
            return True, "✅ 已清除已保存的会话"
        return True, "ℹ️ 会话文件不存在，无需清除"
    except Exception:
        return False, "❌ [WORKSPACE_CLEAR_FAILED] 工作区清除失败，请重试。"
