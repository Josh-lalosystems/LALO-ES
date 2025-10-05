"""Compatibility shim: re-export names from core.tools.base

Some modules import core.tools.base_tool; this file re-exports the canonical
implementations from core.tools.base to maintain backward compatibility.
"""
from .base import (
    BaseTool,
    ToolDefinition,
    ToolParameter,
    ToolExecutionResult,
)

__all__ = [
    "BaseTool",
    "ToolDefinition",
    "ToolParameter",
    "ToolExecutionResult",
]
