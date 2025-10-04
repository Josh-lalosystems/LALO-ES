# Copyright (c) 2025 LALO AI LLC. All rights reserved.
"""
Base tool class and interfaces for LALO AI tool system

All tools must inherit from BaseTool and implement the execute() method.
Tools are automatically discovered and registered at startup.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class ToolParameter(BaseModel):
    """Definition of a tool parameter"""
    name: str
    type: str  # "string", "number", "boolean", "array", "object"
    description: str
    required: bool = True
    default: Optional[Any] = None
    enum: Optional[List[Any]] = None  # For restricted values


class ToolDefinition(BaseModel):
    """Complete tool definition for registration and discovery"""
    name: str = Field(..., description="Unique tool identifier (e.g., 'web_search')")
    description: str = Field(..., description="Human-readable description")
    category: str = Field(default="general", description="Tool category")
    parameters: List[ToolParameter] = Field(default_factory=list)
    returns: Dict[str, Any] = Field(default_factory=dict)
    requires_approval: bool = Field(default=False, description="Requires human approval before execution")
    cost_estimate: Optional[float] = Field(default=None, description="Estimated cost per execution in USD")


class ToolExecutionResult(BaseModel):
    """Result of a tool execution"""
    success: bool
    output: Any = None
    error: Optional[str] = None
    execution_time_ms: Optional[int] = None
    tokens_used: Optional[int] = 0
    cost: Optional[float] = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseTool(ABC):
    """
    Base class for all LALO AI tools

    All tools must:
    1. Inherit from this class
    2. Implement execute() method
    3. Define tool_definition property
    4. Handle errors gracefully
    """

    def __init__(self):
        """Initialize the tool"""
        self._enabled = True
        self._execution_count = 0

    @property
    @abstractmethod
    def tool_definition(self) -> ToolDefinition:
        """
        Define the tool's interface
        Must be implemented by all tools
        """
        pass

    @abstractmethod
    async def execute(self, **kwargs) -> ToolExecutionResult:
        """
        Execute the tool with given parameters

        Args:
            **kwargs: Tool-specific parameters defined in tool_definition

        Returns:
            ToolExecutionResult with success status and output

        Raises:
            Should not raise exceptions - return ToolExecutionResult with error instead
        """
        pass

    async def validate_input(self, **kwargs) -> tuple[bool, Optional[str]]:
        """
        Validate input parameters against tool_definition

        Returns:
            (is_valid, error_message)
        """
        tool_def = self.tool_definition

        # Check required parameters
        for param in tool_def.parameters:
            if param.required and param.name not in kwargs:
                return False, f"Missing required parameter: {param.name}"

            # Type validation (basic)
            if param.name in kwargs:
                value = kwargs[param.name]
                expected_type = param.type

                # Basic type checking
                if expected_type == "string" and not isinstance(value, str):
                    return False, f"Parameter {param.name} must be a string"
                elif expected_type == "number" and not isinstance(value, (int, float)):
                    return False, f"Parameter {param.name} must be a number"
                elif expected_type == "boolean" and not isinstance(value, bool):
                    return False, f"Parameter {param.name} must be a boolean"
                elif expected_type == "array" and not isinstance(value, list):
                    return False, f"Parameter {param.name} must be an array"
                elif expected_type == "object" and not isinstance(value, dict):
                    return False, f"Parameter {param.name} must be an object"

                # Enum validation
                if param.enum and value not in param.enum:
                    return False, f"Parameter {param.name} must be one of {param.enum}"

        return True, None

    async def execute_with_validation(self, **kwargs) -> ToolExecutionResult:
        """
        Execute with automatic input validation and error handling
        This is the method that should be called externally
        """
        start_time = datetime.now()

        # Validate input
        is_valid, error_msg = await self.validate_input(**kwargs)
        if not is_valid:
            return ToolExecutionResult(
                success=False,
                error=f"Validation failed: {error_msg}",
                execution_time_ms=0
            )

        # Execute tool
        try:
            result = await self.execute(**kwargs)
            self._execution_count += 1

            # Calculate execution time if not already set
            if result.execution_time_ms is None:
                elapsed = (datetime.now() - start_time).total_seconds() * 1000
                result.execution_time_ms = int(elapsed)

            return result

        except Exception as e:
            # Catch any unhandled exceptions
            elapsed = (datetime.now() - start_time).total_seconds() * 1000
            return ToolExecutionResult(
                success=False,
                error=f"Unexpected error: {str(e)}",
                execution_time_ms=int(elapsed)
            )

    def is_enabled(self) -> bool:
        """Check if tool is enabled"""
        return self._enabled

    def enable(self):
        """Enable the tool"""
        self._enabled = True

    def disable(self):
        """Disable the tool"""
        self._enabled = False

    def get_execution_count(self) -> int:
        """Get number of times this tool has been executed"""
        return self._execution_count
