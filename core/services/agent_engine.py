# © 2025 LALO AI, LLC. All Rights Reserved
# SPDX-License-Identifier: All-Rights-Reserved

"""
Agent Execution Engine

Executes custom agents with context management, tool access control,
memory, guardrails, and monitoring
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from uuid import uuid4
import asyncio

from core.models.agent import Agent, AgentExecution
from core.services.agent_manager import agent_manager
from core.services.ai_service import ai_service
from core.tools.registry import tool_registry
from core.database import SessionLocal


class AgentContext:
    """
    Maintains context for agent execution
    """

    def __init__(self, agent: Agent, user_id: str):
        self.agent = agent
        self.user_id = user_id
        self.conversation_history: List[Dict[str, str]] = []
        self.tool_calls: List[Dict] = []
        self.iterations = 0
        self.total_tokens = 0
        self.total_cost = 0.0

    def add_message(self, role: str, content: str):
        """Add message to conversation history"""
        self.conversation_history.append({
            "role": role,
            "content": content
        })

    def add_tool_call(self, tool_name: str, tool_input: Dict, tool_output: Any):
        """Record tool usage"""
        self.tool_calls.append({
            "tool": tool_name,
            "input": tool_input,
            "output": tool_output,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    def check_guardrails(self, user_input: str) -> tuple[bool, Optional[str]]:
        """
        Check if input violates any guardrails

        Returns:
            (allowed: bool, reason: Optional[str])
        """
        for guardrail in self.agent.guardrails:
            if guardrail["type"] == "blocked_keywords":
                for keyword in guardrail["keywords"]:
                    if keyword.lower() in user_input.lower():
                        return False, f"Input contains blocked keyword: {keyword}"

            elif guardrail["type"] == "max_length":
                if len(user_input) > guardrail["max_length"]:
                    return False, f"Input exceeds max length: {guardrail['max_length']}"

            elif guardrail["type"] == "required_prefix":
                if not user_input.startswith(guardrail["prefix"]):
                    return False, f"Input must start with: {guardrail['prefix']}"

        return True, None

    def should_continue(self) -> tuple[bool, Optional[str]]:
        """
        Check if execution should continue

        Returns:
            (continue: bool, reason: Optional[str])
        """
        # Check iteration limit
        if self.iterations >= self.agent.max_iterations:
            return False, f"Max iterations reached: {self.agent.max_iterations}"

        # Check token limit (if configured)
        max_total_tokens = 100000  # Hard limit
        if self.total_tokens >= max_total_tokens:
            return False, f"Token limit reached: {max_total_tokens}"

        return True, None


class AgentEngine:
    """
    Agent execution engine
    """

    def __init__(self):
        pass

    async def execute_agent(
        self,
        agent_id: str,
        user_id: str,
        user_input: str,
        context: Optional[Dict] = None
    ) -> Dict:
        """
        Execute an agent with user input

        Args:
            agent_id: Agent to execute
            user_id: User executing the agent
            user_input: User's input/request
            context: Optional execution context

        Returns:
            Execution result dictionary
        """
        # Get agent
        agent = agent_manager.get_agent(agent_id, user_id)
        if not agent:
            raise ValueError("Agent not found or access denied")

        # Create execution context
        agent_context = AgentContext(agent, user_id)

        # Create execution record
        execution = await self._create_execution_record(agent_id, user_id)

        try:
            # Check guardrails
            allowed, reason = agent_context.check_guardrails(user_input)
            if not allowed:
                await self._complete_execution(execution.id, "failed", error_message=reason)
                return {
                    "success": False,
                    "error": reason,
                    "execution_id": execution.id
                }

            # Build conversation with system prompt
            messages = [
                {"role": "system", "content": agent.system_prompt},
                {"role": "user", "content": user_input}
            ]

            # Execute with timeout
            try:
                result = await asyncio.wait_for(
                    self._run_agent_loop(agent, agent_context, messages, user_id),
                    timeout=agent.timeout_seconds
                )

                # Complete execution
                await self._complete_execution(
                    execution.id,
                    "completed",
                    tools_used=[tc["tool"] for tc in agent_context.tool_calls],
                    tokens_used=agent_context.total_tokens,
                    cost=agent_context.total_cost
                )

                # Update usage count
                await self._increment_usage(agent_id)

                return {
                    "success": True,
                    "response": result,
                    "execution_id": execution.id,
                    "tokens_used": agent_context.total_tokens,
                    "cost": agent_context.total_cost,
                    "tools_used": [tc["tool"] for tc in agent_context.tool_calls]
                }

            except asyncio.TimeoutError:
                await self._complete_execution(
                    execution.id,
                    "timeout",
                    error_message=f"Execution exceeded timeout: {agent.timeout_seconds}s"
                )
                return {
                    "success": False,
                    "error": "Execution timeout",
                    "execution_id": execution.id
                }

        except Exception as e:
            await self._complete_execution(
                execution.id,
                "failed",
                error_message=str(e)
            )
            return {
                "success": False,
                "error": str(e),
                "execution_id": execution.id
            }

    async def _run_agent_loop(
        self,
        agent: Agent,
        context: AgentContext,
        messages: List[Dict],
        user_id: str
    ) -> str:
        """
        Run agent execution loop with tool calling

        Args:
            agent: Agent to execute
            context: Agent context
            messages: Conversation messages
            user_id: User ID

        Returns:
            Final response string
        """
        while True:
            # Check if should continue
            should_continue, reason = context.should_continue()
            if not should_continue:
                return f"Execution stopped: {reason}"

            context.iterations += 1

            # Get AI response
            response = await ai_service.generate(
                prompt=messages[-1]["content"] if messages else "",
                model_name=agent.model,
                user_id=user_id,
                max_tokens=agent.max_tokens,
                temperature=agent.temperature,
                top_p=agent.top_p,
                frequency_penalty=agent.frequency_penalty,
                presence_penalty=agent.presence_penalty
            )

            # Track tokens and cost
            context.total_tokens += 1000  # Estimate
            context.total_cost += 0.002   # Estimate

            # Check if response contains tool call (simplified - real implementation would parse function calls)
            if "TOOL_CALL:" in str(response):
                # Parse tool call (simplified)
                tool_name = "web_search"  # Would extract from response

                # Check if agent is allowed to use this tool
                if tool_name not in agent.allowed_tools:
                    return f"Agent not allowed to use tool: {tool_name}"

                # Execute tool
                tool_result = await tool_registry.execute_tool(
                    tool_name,
                    user_permissions=["web_access"],  # Would get from user
                    query="test"  # Would extract from response
                )

                # Record tool usage
                context.add_tool_call(tool_name, {"query": "test"}, tool_result.output)

                # Add tool result to conversation
                messages.append({
                    "role": "assistant",
                    "content": f"Tool result: {tool_result.output}"
                })

                # Continue loop
                continue

            else:
                # No tool call - return response
                return str(response)

    async def _create_execution_record(self, agent_id: str, user_id: str) -> AgentExecution:
        """Create execution record in database"""
        db = SessionLocal()
        try:
            execution = AgentExecution(
                id=str(uuid4()),
                agent_id=agent_id,
                user_id=user_id,
                started_at=datetime.now(timezone.utc),
                status="running"
            )
            db.add(execution)
            db.commit()
            db.refresh(execution)
            return execution
        finally:
            db.close()

    async def _complete_execution(
        self,
        execution_id: str,
        status: str,
        error_message: Optional[str] = None,
        tools_used: Optional[List[str]] = None,
        tokens_used: int = 0,
        cost: float = 0.0
    ):
        """Update execution record on completion"""
        db = SessionLocal()
        try:
            execution = db.query(AgentExecution).filter(
                AgentExecution.id == execution_id
            ).first()

            if execution:
                execution.completed_at = datetime.now(timezone.utc)
                execution.status = status
                execution.error_message = error_message
                execution.tools_used = tools_used or []
                execution.tokens_used = tokens_used
                execution.cost = cost

                # Calculate execution time
                if execution.started_at:
                    delta = execution.completed_at - execution.started_at
                    execution.execution_time_ms = int(delta.total_seconds() * 1000)

                db.commit()
        finally:
            db.close()

    async def _increment_usage(self, agent_id: str):
        """Increment agent usage count"""
        db = SessionLocal()
        try:
            agent = db.query(Agent).filter(Agent.id == agent_id).first()
            if agent:
                agent.usage_count += 1
                db.commit()
        finally:
            db.close()


# Singleton instance
agent_engine = AgentEngine()
