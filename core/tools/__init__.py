# Copyright (c) 2025 LALO AI LLC. All rights reserved.
"""
LALO AI Tool System

This package provides the tool framework for LALO AI:
- Base tool classes and interfaces
- Tool registry for discovery and management
- Individual tool implementations

Available tools:
- web_search: Search the web using Tavily/SerpAPI
- rag_query: Query indexed documents using RAG
- image_generator: Generate images using DALL-E
- code_executor: Execute code in sandboxed environment
- file_operations: Read/write files safely
- database_query: Query databases (read-only)
- api_call: Make HTTP requests to external APIs
"""

from core.tools.base import (
    BaseTool,
    ToolDefinition,
    ToolParameter,
    ToolExecutionResult
)
from core.tools.registry import tool_registry, ToolRegistry
from core.tools.web_search import web_search_tool
from core.tools.rag_tool import rag_tool
from core.tools.image_generator import image_generator_tool
from core.tools.code_executor import code_executor_tool
from core.tools.file_operations import file_operations_tool
from core.tools.database_query import database_query_tool
from core.tools.api_call import api_call_tool

# Register tools
tool_registry.register_tool(web_search_tool, required_permissions=["web_access"])
tool_registry.register_tool(rag_tool, required_permissions=["data_access"])
tool_registry.register_tool(image_generator_tool, required_permissions=["image_generation"])
tool_registry.register_tool(code_executor_tool, required_permissions=["code_execution"])
tool_registry.register_tool(file_operations_tool, required_permissions=["filesystem_access"])
tool_registry.register_tool(database_query_tool, required_permissions=["db_read_only"])
tool_registry.register_tool(api_call_tool, required_permissions=["external_api_access"])

__all__ = [
    "BaseTool",
    "ToolDefinition",
    "ToolParameter",
    "ToolExecutionResult",
    "ToolRegistry",
    "tool_registry",
    "web_search_tool",
    "rag_tool",
    "image_generator_tool",
    "code_executor_tool",
    "file_operations_tool",
    "database_query_tool"
    ,
    "api_call_tool"
]
