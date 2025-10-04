# Copyright (c) 2025 LALO AI LLC. All rights reserved.
"""
File Operations Tool

Provides sandboxed read/write/list/delete of files within an allowed workspace directory.
- Prevents path traversal outside the allowed root
- Enforces file size and type allowlists
- Optional virus scan hook (no-op by default)
"""
from __future__ import annotations

import os
import io
import mimetypes
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from core.tools.base import BaseTool, ToolDefinition, ToolParameter, ToolExecutionResult

# Defaults (can be overridden via env vars later)
ALLOWED_ROOT = os.getenv("FILE_TOOL_ROOT", os.path.abspath("./sandbox"))
MAX_BYTES = int(os.getenv("FILE_TOOL_MAX_BYTES", "2_000_000"))  # ~2MB
ALLOWED_MIME_PREFIXES = [
    "text/",
    "application/json",
    "application/xml",
    "image/png",
    "image/jpeg",
]

os.makedirs(ALLOWED_ROOT, exist_ok=True)

class FileOp(BaseModel):
    op: str  # read, write, list, delete
    path: str
    content: Optional[str] = None  # for write


def _safe_join(root: str, *paths: str) -> str:
    """Join and normalize a path, ensuring it's inside root."""
    candidate = os.path.abspath(os.path.join(root, *paths))
    if not candidate.startswith(os.path.abspath(root) + os.sep) and candidate != os.path.abspath(root):
        raise ValueError("Path traversal detected; access denied")
    return candidate


def _is_allowed_type(path: str) -> bool:
    mime, _ = mimetypes.guess_type(path)
    if mime is None:
        # Unknown types only allowed if text-based path extension
        return any(path.endswith(ext) for ext in [".txt", ".md", ".json", ".csv", ".xml", ".log"])
    return any(mime.startswith(prefix) or mime == prefix for prefix in ALLOWED_MIME_PREFIXES)


class FileOperationsTool(BaseTool):
    @property
    def tool_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="file_operations",
            description="Sandboxed file operations within the workspace (read/write/list/delete)",
            category="filesystem",
            parameters=[
                ToolParameter(name="op", type="string", description="Operation: read|write|list|delete", required=True, enum=["read","write","list","delete"]),
                ToolParameter(name="path", type="string", description="Relative file or directory path under sandbox root", required=True),
                ToolParameter(name="content", type="string", description="Content to write (when op=write)", required=False),
            ],
            returns={"result": "Operation result (content, listing, or confirmation)"},
            requires_approval=False,
        )

    async def execute(self, **kwargs) -> ToolExecutionResult:
        try:
            op = kwargs.get("op")
            rel_path = kwargs.get("path")
            content = kwargs.get("content")

            target = _safe_join(ALLOWED_ROOT, rel_path)

            if op == "list":
                if not os.path.exists(target):
                    return ToolExecutionResult(success=False, error="Path not found")
                if os.path.isfile(target):
                    return ToolExecutionResult(success=True, output={"type": "file", "path": rel_path, "size": os.path.getsize(target)})
                # directory
                items = []
                for name in os.listdir(target):
                    full = os.path.join(target, name)
                    items.append({
                        "name": name,
                        "is_dir": os.path.isdir(full),
                        "size": os.path.getsize(full) if os.path.isfile(full) else None
                    })
                return ToolExecutionResult(success=True, output={"type": "dir", "path": rel_path, "items": items})

            if op == "read":
                if not os.path.isfile(target):
                    return ToolExecutionResult(success=False, error="File not found")
                if not _is_allowed_type(target):
                    return ToolExecutionResult(success=False, error="Disallowed file type")
                if os.path.getsize(target) > MAX_BYTES:
                    return ToolExecutionResult(success=False, error="File too large")
                with io.open(target, "r", encoding="utf-8", errors="replace") as f:
                    data = f.read()
                return ToolExecutionResult(success=True, output={"path": rel_path, "content": data})

            if op == "write":
                if content is None:
                    return ToolExecutionResult(success=False, error="Missing content for write")
                # Ensure parent dirs
                os.makedirs(os.path.dirname(target), exist_ok=True)
                # Type check based on extension
                if not _is_allowed_type(target):
                    return ToolExecutionResult(success=False, error="Disallowed file type for write")
                data_bytes = content.encode("utf-8", errors="replace")
                if len(data_bytes) > MAX_BYTES:
                    return ToolExecutionResult(success=False, error="Content too large")
                with io.open(target, "w", encoding="utf-8") as f:
                    f.write(content)
                return ToolExecutionResult(success=True, output={"path": rel_path, "bytes": len(data_bytes)})

            if op == "delete":
                if os.path.isdir(target):
                    return ToolExecutionResult(success=False, error="Refusing to delete directories for safety")
                if not os.path.isfile(target):
                    return ToolExecutionResult(success=False, error="File not found")
                os.remove(target)
                return ToolExecutionResult(success=True, output={"deleted": rel_path})

            return ToolExecutionResult(success=False, error="Unknown operation")
        except Exception as e:
            return ToolExecutionResult(success=False, error=str(e))


# Singleton instance for registry
file_operations_tool = FileOperationsTool()
