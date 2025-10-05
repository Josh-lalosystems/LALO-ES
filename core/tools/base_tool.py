"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

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
