# Copyright (c) 2025 LALO AI LLC. All rights reserved.
"""
Tool Registry - Central management for all LALO AI tools

The registry:
- Discovers and registers all available tools
- Validates tool definitions
- Provides tool lookup and execution
- Enforces permissions and rate limits
- Tracks usage and performance
"""

from typing import Dict, List, Optional, Type
from core.tools.base import BaseTool, ToolExecutionResult, ToolDefinition
import logging

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Singleton registry for all system tools
    Manages tool discovery, registration, and execution
    """

    _instance = None
    _tools: Dict[str, BaseTool] = {}
    _tool_permissions: Dict[str, List[str]] = {}  # tool_name -> list of required permissions

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ToolRegistry, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._tools = {}
        self._tool_permissions = {}
        self._initialized = True
        logger.info("ToolRegistry initialized")

    def register_tool(self, tool: BaseTool, required_permissions: List[str] = None):
        """
        Register a tool with the system

        Args:
            tool: Instance of BaseTool
            required_permissions: List of permissions required to use this tool

        Raises:
            ValueError: If tool name already registered or invalid definition
        """
        tool_def = tool.tool_definition

        if tool_def.name in self._tools:
            raise ValueError(f"Tool '{tool_def.name}' is already registered")

        # Validate tool definition
        if not tool_def.name or not tool_def.description:
            raise ValueError("Tool must have name and description")

        self._tools[tool_def.name] = tool
        self._tool_permissions[tool_def.name] = required_permissions or []

        logger.info(f"Registered tool: {tool_def.name} ({tool_def.category})")

    def unregister_tool(self, tool_name: str):
        """Remove a tool from the registry"""
        if tool_name in self._tools:
            del self._tools[tool_name]
            del self._tool_permissions[tool_name]
            logger.info(f"Unregistered tool: {tool_name}")

    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """Get a tool by name"""
        return self._tools.get(tool_name)

    def get_all_tools(self) -> Dict[str, BaseTool]:
        """Get all registered tools"""
        return self._tools.copy()

    def get_tool_permissions(self, tool_name: str) -> List[str]:
        """Get required permissions for a tool by name"""
        return self._tool_permissions.get(tool_name, [])

    def get_tool_info(self, tool_name: str) -> Optional[dict]:
        """Get a summary of a tool including permissions and status"""
        tool = self.get_tool(tool_name)
        if not tool:
            return None
        td = tool.tool_definition
        return {
            "name": td.name,
            "description": td.description,
            "category": td.category,
            "enabled": tool.is_enabled(),
            "required_permissions": self.get_tool_permissions(td.name),
            "execution_count": tool.get_execution_count(),
            "parameters": [
                {
                    "name": p.name,
                    "type": p.type,
                    "description": p.description,
                    "required": p.required,
                    "default": p.default,
                    "enum": p.enum,
                }
                for p in td.parameters
            ],
        }

    def list_tools_info(self) -> List[dict]:
        """List info for all registered tools"""
        return [self.get_tool_info(name) for name in self._tools.keys()]

    def get_tool_definitions(self) -> List[ToolDefinition]:
        """Get definitions of all registered tools"""
        return [tool.tool_definition for tool in self._tools.values()]

    def get_tools_by_category(self, category: str) -> List[BaseTool]:
        """Get all tools in a specific category"""
        return [
            tool for tool in self._tools.values()
            if tool.tool_definition.category == category
        ]

    def get_enabled_tools(self) -> List[BaseTool]:
        """Get all currently enabled tools"""
        return [tool for tool in self._tools.values() if tool.is_enabled()]

    def is_tool_enabled(self, tool_name: str) -> bool:
        tool = self.get_tool(tool_name)
        return bool(tool and tool.is_enabled())

    def enable_tool(self, tool_name: str) -> bool:
        """Enable a registered tool; returns True if changed or already enabled."""
        tool = self.get_tool(tool_name)
        if not tool:
            return False
        tool.enable()
        logger.info("Enabled tool: %s", tool_name)
        return True

    def disable_tool(self, tool_name: str) -> bool:
        """Disable a registered tool; returns True if changed or already disabled."""
        tool = self.get_tool(tool_name)
        if not tool:
            return False
        tool.disable()
        logger.info("Disabled tool: %s", tool_name)
        return True

    async def execute_tool(
        self,
        tool_name: str,
        user_permissions: List[str] = None,
        **kwargs
    ) -> ToolExecutionResult:
        """
        Execute a tool with permission checking

        Args:
            tool_name: Name of tool to execute
            user_permissions: List of user's permissions
            **kwargs: Tool-specific parameters

        Returns:
            ToolExecutionResult
        """
        # Get tool
        tool = self.get_tool(tool_name)
        if not tool:
            return ToolExecutionResult(
                success=False,
                error=f"Tool '{tool_name}' not found"
            )

        # Check if tool is enabled
        if not tool.is_enabled():
            return ToolExecutionResult(
                success=False,
                error=f"Tool '{tool_name}' is currently disabled"
            )

        # Check permissions
        required_perms = self._tool_permissions.get(tool_name, [])
        user_perms = user_permissions or []

        if required_perms and not any(perm in user_perms for perm in required_perms):
            return ToolExecutionResult(
                success=False,
                error=f"Insufficient permissions to use tool '{tool_name}'. Required: {required_perms}"
            )

        # Execute tool with validation
        try:
            result = await tool.execute_with_validation(**kwargs)
            return result
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return ToolExecutionResult(
                success=False,
                error=f"Tool execution failed: {str(e)}"
            )

    def get_tool_schema(self, tool_name: str) -> Optional[Dict]:
        """
        Get JSON schema for a tool (for LLM function calling)

        Returns OpenAI-compatible function schema
        """
        tool = self.get_tool(tool_name)
        if not tool:
            return None

        tool_def = tool.tool_definition

        # Build parameters schema
        properties = {}
        required = []

        for param in tool_def.parameters:
            properties[param.name] = {
                "type": param.type,
                "description": param.description
            }

            if param.enum:
                properties[param.name]["enum"] = param.enum

            if param.required:
                required.append(param.name)

        schema = {
            "type": "function",
            "function": {
                "name": tool_def.name,
                "description": tool_def.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        }

        return schema

    def get_all_tool_schemas(self) -> List[Dict]:
        """Get schemas for all enabled tools"""
        schemas = []
        for tool in self.get_enabled_tools():
            schema = self.get_tool_schema(tool.tool_definition.name)
            if schema:
                schemas.append(schema)
        return schemas


# Global registry instance
tool_registry = ToolRegistry()
