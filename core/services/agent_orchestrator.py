"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

"""
Agent Orchestrator - coordinates agents, workflows and execution.

This is intentionally lightweight: it delegates execution to the pluggable
executor and manages assignment through the runtime agent manager.
"""
from typing import Dict, Any, Tuple
import logging

from core.services.agent_runtime import runtime_agent_manager
from core.services.executor import default_executor, start_executor_worker

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    def __init__(self, start_worker: bool = True):
        self.executor_stop_event = None
        if start_worker:
            self.executor_stop_event = start_executor_worker(default_executor)
            logger.info("AgentOrchestrator started executor worker")

    def assign_task(self, agent_type: str, task: Dict[str, Any]) -> Tuple[str, str]:
        """Assign a task to an agent of the requested type (creates one if needed)."""
        agent_id, task_id = runtime_agent_manager.assign_task(agent_type, task)
        logger.info("Orchestrator assigned task %s to agent %s", task_id, agent_id)
        return agent_id, task_id


# Global instance used by routes
agent_orchestrator = AgentOrchestrator()
"""
Agent Orchestrator - Coordinates multi-model, multi-tool workflows

Integrates with:
- RouterModel (my Phase 1) for routing decisions
- AgentManager (team's work) for agent lifecycle
- WorkflowManager (team's work) for state management
- LocalInferenceServer (my Phase 1) for model execution
- ConfidenceModel (my Phase 2) for output validation
"""

import json
import logging
import asyncio
from typing import Dict, List, Optional, Any, AsyncGenerator
from uuid import uuid4
from datetime import datetime

from core.services.router_model import router_model
from core.services.local_llm_service import local_llm_service
from core.services.confidence_model import confidence_model

logger = logging.getLogger(__name__)

# Will integrate with team's work when available
try:
    from core.services.agent_manager import agent_manager
    AGENT_MANAGER_AVAILABLE = True
except ImportError:
    agent_manager = None
    AGENT_MANAGER_AVAILABLE = False
    logger.warning("AgentManager not available - using standalone mode")

try:
    from core.services.workflow_state import workflow_manager
    WORKFLOW_MANAGER_AVAILABLE = True
except ImportError:
    workflow_manager = None
    WORKFLOW_MANAGER_AVAILABLE = False
    logger.warning("WorkflowManager not available - using standalone mode")


class AgentOrchestrator:
    """
    Coordinates complex multi-step workflows

    Responsibilities:
    - Workflow planning (break down complex requests)
    - Model selection for each step
    - Tool/MCP coordination
    - Parallel execution management
    - Result aggregation
    - Confidence validation
    """

    def __init__(self):
        self.router = router_model
        self.inference_server = local_llm_service
        self.confidence = confidence_model
        self.agent_manager = agent_manager if AGENT_MANAGER_AVAILABLE else None
        self.workflow_manager = workflow_manager if WORKFLOW_MANAGER_AVAILABLE else None
        logger.info(f"AgentOrchestrator initialized (AgentManager: {AGENT_MANAGER_AVAILABLE}, WorkflowManager: {WORKFLOW_MANAGER_AVAILABLE})")

    async def execute_complex_request(
        self,
        user_request: str,
        routing_decision: Dict,
        user_id: str,
        available_models: List[str],
        stream: bool = False
    ) -> Dict:
        """
        Execute complex request through multi-step workflow

        Args:
            user_request: Original user request
            routing_decision: Router's decision dict
            user_id: User ID for context
            available_models: List of available model names
            stream: Whether to stream results

        Returns:
            {
                "response": str,
                "workflow_id": str,
                "steps_completed": int,
                "models_used": [str],
                "confidence": float,
                "metadata": {...}
            }
        """
        logger.info(f"Executing complex request: {user_request[:100]}...")

        # Step 1: Plan the workflow
        plan = await self._plan_workflow(user_request, routing_decision, available_models)
        logger.info(f"Workflow plan created: {len(plan['steps'])} steps")

        # Step 2: Create workflow if manager available
        workflow_id = None
        if self.workflow_manager:
            workflow_id = self.workflow_manager.create_workflow(
                name=f"Request: {user_request[:50]}",
                steps=plan["steps"]
            )
            self.workflow_manager.start_workflow(workflow_id)

        # Step 3: Execute plan
        results = await self._execute_plan(
            plan,
            user_request,
            user_id,
            workflow_id,
            stream=stream
        )

        # Step 4: Validate final output
        final_output = results.get("final_output", "")
        confidence_score = await self.confidence.score(
            output=final_output,
            original_request=user_request,
            context={"workflow_id": workflow_id, "steps": len(plan["steps"])}
        )

        # Step 5: Handle low confidence (retry or escalate)
        if self.confidence.should_retry(confidence_score["confidence"]):
            logger.warning(f"Low confidence ({confidence_score['confidence']:.2f}), considering retry")
            # For now, log warning. In future, implement retry logic

        return {
            "response": final_output,
            "workflow_id": workflow_id,
            "steps_completed": results.get("steps_completed", 0),
            "models_used": results.get("models_used", []),
            "confidence": confidence_score["confidence"],
            "confidence_details": confidence_score,
            "metadata": {
                "plan": plan,
                "routing_decision": routing_decision,
                "execution_time_ms": results.get("execution_time_ms", 0)
            }
        }

    async def _plan_workflow(
        self,
        user_request: str,
        routing_decision: Dict,
        available_models: List[str]
    ) -> Dict:
        """
        Create execution plan for complex request

        Uses local model to decompose request into steps
        """
        # Get recommended model from routing decision
        planner_model = routing_decision.get("recommended_model", "liquid-tool")
        # Normalize planner_model base name (allow 'tinyllama-1.1b' -> 'tinyllama')
        if "-" in planner_model:
            planner_model = planner_model.split("-")[0]

        # If recommended model not available, use first available
        if planner_model not in available_models and available_models:
            planner_model = available_models[0]

        prompt = f"""<|system|>
You are a workflow planner. Break down the user request into a sequence of executable steps.

Each step should specify:
1. action: The type of action (generate, search, extract, analyze, etc.)
2. model: Which model to use (from available models)
3. description: What this step does
4. dependencies: Which step IDs must complete first (empty array if none)
5. parallel: Can this run in parallel with other steps? (true/false)

Available models: {', '.join(available_models)}

Respond ONLY with valid JSON:
{{
  "steps": [
    {{
      "id": 1,
      "action": "generate",
      "model": "tinyllama-1.1b",
      "description": "Generate initial analysis",
      "dependencies": [],
      "parallel": false
    }}
  ]
}}
<|user|>
Request: {user_request}

Routing Info: Complexity={routing_decision.get('complexity', 0.5):.2f}, Path={routing_decision.get('path')}
<|assistant|>
"""

        try:
            # Use local inference for planning
            result = await self.inference_server.generate(
                prompt=prompt,
                model_name=planner_model,
                max_tokens=512,
                temperature=0.3
            )

            # Parse JSON plan
            plan = json.loads(result.strip())

            # Validate plan structure
            if "steps" not in plan or not plan["steps"]:
                logger.warning("Invalid plan from model, using default")
                plan = self._create_default_plan(user_request, available_models)

            return plan

        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"Plan creation failed: {e}, using default")
            return self._create_default_plan(user_request, available_models)

    def _create_default_plan(self, user_request: str, available_models: List[str]) -> Dict:
        """Create simple fallback plan"""
        model = available_models[0] if available_models else "tinyllama"

        return {
            "steps": [
                {
                    "id": 1,
                    "action": "generate",
                    "model": model,
                    "description": f"Provide a clear answer to: {user_request}",
                    "dependencies": [],
                    "parallel": False
                }
            ]
        }

    async def _execute_plan(
        self,
        plan: Dict,
        user_request: str,
        user_id: str,
        workflow_id: Optional[str],
        stream: bool = False
    ) -> Dict:
        """
        Execute the planned workflow

        Handles:
        - Sequential execution
        - Parallel execution (future)
        - Error handling and retries
        - Confidence checking at key steps
        """
        start_time = datetime.now()
        results = {}
        final_output = ""
        models_used = []

        for step in plan["steps"]:
            step_id = step["id"]
            action = step["action"]
            model = step["model"]
            description = step["description"]

            logger.info(f"Executing step {step_id}: {description}")

            # Check dependencies
            dependencies = step.get("dependencies", [])
            if not self._dependencies_met(dependencies, results):
                logger.warning(f"Step {step_id} dependencies not met, skipping")
                continue

            # Execute step based on action type
            try:
                if action == "generate":
                    # Build prompt with context from previous steps
                    context = self._build_step_context(results, user_request)
                    prompt = f"{context}\n\nRequest: {description}"

                    output = await self.inference_server.generate(
                        prompt=prompt,
                        model_name=model,
                        max_tokens=512,
                        temperature=0.7
                    )

                    results[step_id] = {
                        "output": output,
                        "model": model,
                        "action": action
                    }

                    final_output = output  # Last output is final
                    if model not in models_used:
                        models_used.append(model)

                    # Update workflow state if available
                    if self.workflow_manager and workflow_id:
                        workflow = self.workflow_manager.get_workflow(workflow_id)
                        if workflow:
                            workflow.steps[str(step_id)].complete(output)

                else:
                    # For other actions (search, extract, etc.), implement later
                    logger.warning(f"Action '{action}' not yet implemented, skipping")
                    results[step_id] = {
                        "output": f"(Action {action} pending implementation)",
                        "model": model,
                        "action": action
                    }

            except Exception as e:
                logger.error(f"Step {step_id} failed: {e}")
                results[step_id] = {
                    "output": f"(Error: {str(e)})",
                    "model": model,
                    "action": action,
                    "error": str(e)
                }

        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds() * 1000  # ms

        return {
            "final_output": final_output,
            "steps_completed": len(results),
            "models_used": models_used,
            "execution_time_ms": execution_time,
            "step_results": results
        }

    def _dependencies_met(self, dependencies: List[int], results: Dict) -> bool:
        """Check if all dependencies are completed"""
        return all(dep in results for dep in dependencies)

    def _build_step_context(self, results: Dict, user_request: str) -> str:
        """Build context from previous step results"""
        if not results:
            return f"Original request: {user_request}"

        context_parts = [f"Original request: {user_request}", "\nPrevious steps:"]

        for step_id, result in results.items():
            output = result.get("output", "")
            context_parts.append(f"Step {step_id}: {output[:200]}")

        return "\n".join(context_parts)

    async def execute_simple_request(
        self,
        user_request: str,
        routing_decision: Dict,
        user_id: str,
        available_models: List[str]
    ) -> Dict:
        """
        Execute simple request (direct model call)

        Simpler than complex workflow - just call model and validate
        """
        model = routing_decision.get("recommended_model", "tinyllama-1.1b")

        # Ensure model is available
        if model not in available_models and available_models:
            model = available_models[0]

        logger.info(f"Executing simple request with {model}")

        try:
            # Generate response
            output = await self.inference_server.generate(
                prompt=user_request,
                model_name=model,
                max_tokens=512,
                temperature=0.7
            )

            # Quick confidence check
            confidence_score = await self.confidence.score(
                output=output,
                original_request=user_request,
                model_used=model
            )

            return {
                "response": output,
                "model": model,
                "confidence": confidence_score["confidence"],
                "confidence_details": confidence_score,
                "path": "simple"
            }

        except Exception as e:
            logger.error(f"Simple request execution failed: {e}")
            raise RuntimeError(f"Failed to execute simple request: {e}")


# Global instance
agent_orchestrator = AgentOrchestrator()
