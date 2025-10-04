# Copyright (c) 2025 LALO AI LLC. All rights reserved.
"""
Tool Executor Service

Safely executes tools with verification and rollback capability.
This is Step 3 of the LALO workflow (execution phase):
1. Create backup/snapshot before execution
2. Execute tool with parameters
3. Verify result meets expectations
4. Rollback if verification fails or error occurs
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime
from core.tools import tool_registry, ToolExecutionResult
from core.database import SessionLocal, ToolExecution
from core.services.microservices_client import mcp_client
import logging
import json
import uuid
import shutil
import os

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Result of executing an action step"""
    success: bool
    step_number: int
    tool_name: str
    tool_output: Any
    verification_passed: bool
    error: Optional[str] = None
    backup_id: Optional[str] = None
    backup_restored: bool = False
    execution_time_ms: Optional[int] = None
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ToolExecutor:
    """
    Executes tools safely with verification and rollback

    Key features:
    - Backup before execution
    - Tool execution via registry
    - Result verification
    - Automatic rollback on failure
    - Comprehensive audit logging
    """

    def __init__(self, backup_dir: str = "./backups"):
        """
        Initialize tool executor

        Args:
            backup_dir: Directory for storing backups
        """
        self.backup_dir = backup_dir
        os.makedirs(backup_dir, exist_ok=True)

    async def execute_plan(
        self,
        action_plan: Any,  # ActionPlan from action_planner
        user_id: str,
        workflow_session_id: str,
        human_approval: bool = True
    ) -> List[ExecutionResult]:
        """
        Execute complete action plan step by step

        Args:
            action_plan: ActionPlan with steps to execute
            user_id: User ID
            workflow_session_id: Workflow session ID for tracking
            human_approval: Whether human approved the plan

        Returns:
            List of ExecutionResult for each step
        """
        logger.info(f"Executing plan with {len(action_plan.steps)} steps for user {user_id}")

        results = []

        for step in action_plan.steps:
            step_num = step.get("step", 0)
            logger.info(f"Executing step {step_num}: {step.get('action', 'unknown')[:100]}...")

            result = await self.execute_step(
                step=step,
                user_id=user_id,
                workflow_session_id=workflow_session_id
            )

            results.append(result)

            # Stop execution if step failed and couldn't be recovered
            if not result.success and not result.backup_restored:
                logger.error(f"Step {step_num} failed fatally. Stopping execution.")
                break

        return results

    async def execute_step(
        self,
        step: Dict,
        user_id: str,
        workflow_session_id: str
    ) -> ExecutionResult:
        """
        Execute a single action step with backup and verification

        Args:
            step: Step dictionary with action, tool, expected_outcome
            user_id: User ID
            workflow_session_id: Workflow session ID

        Returns:
            ExecutionResult with success status and details
        """
        start_time = datetime.now()
        step_num = step.get("step", 0)
        action = step.get("action", "")
        tool_name = step.get("tool", "auto")
        expected_outcome = step.get("expected_outcome", "")

        # Create backup
        backup_id = await self._create_backup(workflow_session_id)

        try:
            # Determine which tool to use
            if tool_name == "auto":
                tool_name = await self._determine_tool(action)

            logger.info(f"Using tool: {tool_name}")

            # Execute tool
            tool_result = await self._execute_tool(
                tool_name=tool_name,
                action=action,
                user_id=user_id,
                workflow_session_id=workflow_session_id
            )

            if not tool_result.success:
                # Tool execution failed
                logger.error(f"Tool execution failed: {tool_result.error}")

                # Attempt rollback
                await self._restore_backup(backup_id)

                elapsed = (datetime.now() - start_time).total_seconds() * 1000
                return ExecutionResult(
                    success=False,
                    step_number=step_num,
                    tool_name=tool_name,
                    tool_output=None,
                    verification_passed=False,
                    error=tool_result.error,
                    backup_id=backup_id,
                    backup_restored=True,
                    execution_time_ms=int(elapsed)
                )

            # Verify result
            verification = await self._verify_result(
                tool_output=tool_result.output,
                expected_outcome=expected_outcome,
                user_id=user_id
            )

            if not verification["passed"]:
                # Verification failed - rollback
                logger.warning(f"Verification failed: {verification['reason']}")

                await self._restore_backup(backup_id)

                elapsed = (datetime.now() - start_time).total_seconds() * 1000
                return ExecutionResult(
                    success=False,
                    step_number=step_num,
                    tool_name=tool_name,
                    tool_output=tool_result.output,
                    verification_passed=False,
                    error=f"Verification failed: {verification['reason']}",
                    backup_id=backup_id,
                    backup_restored=True,
                    execution_time_ms=int(elapsed)
                )

            # Success!
            elapsed = (datetime.now() - start_time).total_seconds() * 1000
            return ExecutionResult(
                success=True,
                step_number=step_num,
                tool_name=tool_name,
                tool_output=tool_result.output,
                verification_passed=True,
                backup_id=backup_id,
                execution_time_ms=int(elapsed),
                metadata={
                    "tokens_used": tool_result.tokens_used,
                    "cost": tool_result.cost
                }
            )

        except Exception as e:
            # Unexpected error - rollback
            logger.error(f"Unexpected error executing step: {e}")

            await self._restore_backup(backup_id)

            elapsed = (datetime.now() - start_time).total_seconds() * 1000
            return ExecutionResult(
                success=False,
                step_number=step_num,
                tool_name=tool_name,
                tool_output=None,
                verification_passed=False,
                error=f"Unexpected error: {str(e)}",
                backup_id=backup_id,
                backup_restored=True,
                execution_time_ms=int(elapsed)
            )

    async def _create_backup(self, workflow_session_id: str) -> str:
        """
        Create backup/snapshot before execution

        For now, just creates a backup ID. In production, would:
        - Snapshot database state
        - Save file system state
        - Record current configurations
        """
        backup_id = f"backup_{workflow_session_id}_{uuid.uuid4().hex[:8]}"
        backup_path = os.path.join(self.backup_dir, backup_id)

        # Create backup directory
        os.makedirs(backup_path, exist_ok=True)

        # TODO: Implement actual backup logic
        # For MVP, just creating placeholder

        logger.info(f"Created backup: {backup_id}")
        return backup_id

    async def _restore_backup(self, backup_id: str):
        """
        Restore from backup

        In production would:
        - Restore database state
        - Restore file system
        - Revert configurations
        """
        logger.info(f"Restoring backup: {backup_id}")

        # TODO: Implement actual restore logic
        # For MVP, just logging

    async def _determine_tool(self, action: str) -> str:
        """
        Determine which tool to use for an action

        Uses simple keyword matching. In production would use LLM.

        Args:
            action: Action description

        Returns:
            Tool name
        """
        action_lower = action.lower()

        # Simple keyword matching
        if any(word in action_lower for word in ["search", "find", "look up", "google", "web"]):
            return "web_search"
        elif any(word in action_lower for word in ["query", "database", "sql", "data"]):
            return "database_query"
        elif any(word in action_lower for word in ["image", "picture", "photo", "generate", "create visual"]):
            return "image_generator"
        elif any(word in action_lower for word in ["code", "execute", "run", "python", "script"]):
            return "code_executor"
        elif any(word in action_lower for word in ["file", "read", "write", "save", "load"]):
            return "file_operations"
        elif any(word in action_lower for word in ["api", "http", "request", "call"]):
            return "api_call"
        elif any(word in action_lower for word in ["document", "retrieve", "knowledge", "rag"]):
            return "rag_query"
        else:
            # Default to web search
            return "web_search"

    async def _execute_tool(
        self,
        tool_name: str,
        action: str,
        user_id: str,
        workflow_session_id: str
    ) -> ToolExecutionResult:
        """
        Execute a tool and log to database

        Args:
            tool_name: Name of tool to execute
            action: Action description (will be parsed for parameters)
            user_id: User ID
            workflow_session_id: Workflow session ID

        Returns:
            ToolExecutionResult
        """
        # Create execution record
        execution_id = str(uuid.uuid4())
        db = SessionLocal()

        try:
            # Create database record
            execution_record = ToolExecution(
                id=execution_id,
                workflow_session_id=workflow_session_id,
                user_id=user_id,
                tool_name=tool_name,
                tool_input={"action": action},
                status="running",
                started_at=datetime.utcnow()
            )
            db.add(execution_record)
            db.commit()

            # Execute via tool registry
            # Note: In production, would parse action to extract parameters
            # For MVP, just passing action as query/prompt

            result = await tool_registry.execute_tool(
                tool_name=tool_name,
                query=action,  # Simple approach: action description as query
                user_id=user_id
            )

            # Update execution record
            execution_record.status = "success" if result.success else "failed"
            execution_record.tool_output = {"result": str(result.output)} if result.output else {}
            execution_record.error_message = result.error
            execution_record.completed_at = datetime.utcnow()
            execution_record.execution_time_ms = result.execution_time_ms
            execution_record.tokens_used = result.tokens_used
            execution_record.cost = result.cost
            db.commit()

            return result

        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")

            # Update record with error
            if execution_record:
                execution_record.status = "failed"
                execution_record.error_message = str(e)
                execution_record.completed_at = datetime.utcnow()
                db.commit()

            return ToolExecutionResult(
                success=False,
                error=str(e)
            )

        finally:
            db.close()

    async def _verify_result(
        self,
        tool_output: Any,
        expected_outcome: str,
        user_id: str
    ) -> Dict:
        """
        Verify tool result matches expected outcome

        In production, would use LLM to compare output with expectations.
        For MVP, just checking if output exists.

        Args:
            tool_output: Tool execution output
            expected_outcome: Expected outcome description
            user_id: User ID

        Returns:
            Dict with "passed" (bool) and "reason" (str)
        """
        # Simple verification: Check if we got any output
        if tool_output is None or (isinstance(tool_output, str) and not tool_output.strip()):
            return {
                "passed": False,
                "reason": "No output generated"
            }

        # Check for error indicators
        if isinstance(tool_output, dict) and tool_output.get("error"):
            return {
                "passed": False,
                "reason": f"Tool returned error: {tool_output.get('error')}"
            }

        # For MVP: If we got non-empty output, consider it verified
        # TODO: Implement LLM-based verification in production
        return {
            "passed": True,
            "reason": "Output generated successfully"
        }


# Global tool executor instance
tool_executor = ToolExecutor()
