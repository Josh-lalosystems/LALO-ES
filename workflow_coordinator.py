"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

# © 2025 LALO AI, LLC. All Rights Reserved
# SPDX-License-Identifier: All-Rights-Reserved

"""
Module: WorkflowCoordinator

Purpose:
- Coordinates between confidence system, memory manager, and agent runtime
- Manages workflow state transitions
- Handles feedback collection at each stage
- Ensures proper data flow between components
"""

from typing import Dict, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
import asyncio
from datetime import datetime

from confidence_system import ConfidenceSystem, InterpretationResult
from enhanced_memory_manager import EnhancedMemoryManager
from agent_runtime import AgentRuntime
from agent_factory import AgentFactory
from audit_logger import AuditLogger

class WorkflowState(Enum):
    INTERPRETING = "interpreting"
    PLANNING = "planning"
    EXECUTING = "executing"
    REVIEWING = "reviewing"
    COMPLETED = "completed"
    ERROR = "error"

@dataclass
class WorkflowContext:
    session_id: str
    current_state: WorkflowState
    interpretation: Optional[InterpretationResult] = None
    plan: Optional[Dict] = None
    execution_results: Optional[Dict] = None
    feedback_history: list = None
    
    def __post_init__(self):
        self.feedback_history = self.feedback_history or []

class WorkflowCoordinator:
    def __init__(self):
        self.confidence_system = ConfidenceSystem()
        self.memory_manager = EnhancedMemoryManager()
        self.agent_factory = AgentFactory()
        self.audit = AuditLogger()
        self.active_workflows = {}

    async def start_workflow(self, user_request: str) -> Tuple[str, WorkflowContext]:
        """
        Initiates a new workflow from a user request
        Returns: (session_id, initial_context)
        """
        # Create new session
        session_id = self.memory_manager.start_session()
        
        # Create initial workflow context
        context = WorkflowContext(
            session_id=session_id,
            current_state=WorkflowState.INTERPRETING
        )
        
        self.active_workflows[session_id] = context
        
        # Start interpretation
        try:
            interpretation = await self.confidence_system.interpret_request(user_request)
            context.interpretation = interpretation
            
            # Record in session memory
            self.memory_manager.record_step(session_id, {
                "state": context.current_state.value,
                "user_request": user_request,
                "interpretation": interpretation.__dict__
            })
            
        except Exception as e:
            context.current_state = WorkflowState.ERROR
            self.audit.log_error(session_id, str(e))
            raise
            
        return session_id, context

    async def process_feedback(self, 
                             session_id: str, 
                             feedback: Dict,
                             stage: WorkflowState) -> WorkflowContext:
        """
        Processes user feedback for any workflow stage
        """
        context = self.active_workflows.get(session_id)
        if not context:
            raise ValueError(f"No active workflow for session {session_id}")
            
        # Record feedback
        self.memory_manager.record_feedback(session_id, {
            "stage": stage.value,
            "feedback": feedback,
            "timestamp": datetime.now(datetime.timezone.utc).isoformat()
        })
        
        context.feedback_history.append({
            "stage": stage.value,
            "feedback": feedback
        })
        
        # Update confidence metrics based on feedback
        if stage == WorkflowState.INTERPRETING:
            await self._handle_interpretation_feedback(context, feedback)
        elif stage == WorkflowState.PLANNING:
            await self._handle_planning_feedback(context, feedback)
        elif stage == WorkflowState.EXECUTING:
            await self._handle_execution_feedback(context, feedback)
        elif stage == WorkflowState.REVIEWING:
            await self._handle_review_feedback(context, feedback)
            
        return context

    async def advance_workflow(self, session_id: str) -> WorkflowContext:
        """
        Advances workflow to next state based on current state and confidence
        """
        context = self.active_workflows.get(session_id)
        if not context:
            raise ValueError(f"No active workflow for session {session_id}")
            
        try:
            if context.current_state == WorkflowState.INTERPRETING:
                if self.confidence_system.requires_clarification(context.interpretation):
                    return context  # Stay in INTERPRETING state
                context.current_state = WorkflowState.PLANNING
                await self._start_planning(context)
                
            elif context.current_state == WorkflowState.PLANNING:
                if not context.plan or self._requires_plan_clarification(context):
                    return context  # Stay in PLANNING state
                context.current_state = WorkflowState.EXECUTING
                await self._start_execution(context)
                
            elif context.current_state == WorkflowState.EXECUTING:
                if not context.execution_results:
                    return context  # Stay in EXECUTING state
                context.current_state = WorkflowState.REVIEWING
                
            elif context.current_state == WorkflowState.REVIEWING:
                context.current_state = WorkflowState.COMPLETED
                await self._complete_workflow(context)
                
        except Exception as e:
            context.current_state = WorkflowState.ERROR
            self.audit.log_error(session_id, str(e))
            raise
            
        return context

    async def _handle_interpretation_feedback(self, 
                                           context: WorkflowContext, 
                                           feedback: Dict):
        """
        Updates interpretation based on user feedback
        """
        if feedback.get("requires_clarification", False):
            # Store the clarification request
            context.interpretation.feedback_required = True
            context.interpretation.suggested_clarifications.extend(
                feedback.get("clarification_points", [])
            )
        else:
            # Update confidence based on positive feedback
            context.interpretation.confidence_score = max(
                context.interpretation.confidence_score,
                feedback.get("confidence_override", 0.0)
            )

    async def _handle_planning_feedback(self, 
                                      context: WorkflowContext, 
                                      feedback: Dict):
        """
        Updates plan based on user feedback
        """
        if feedback.get("approved", False):
            context.plan["confidence_score"] = max(
                context.plan.get("confidence_score", 0.0),
                feedback.get("confidence_score", 0.0)
            )
        else:
            context.plan["requires_revision"] = True
            context.plan["revision_notes"] = feedback.get("revision_notes", [])

    async def _handle_execution_feedback(self, 
                                       context: WorkflowContext, 
                                       feedback: Dict):
        """
        Processes execution feedback and handles any necessary corrections
        """
        if not feedback.get("success", True):
            # Record execution issues
            context.execution_results["issues"] = feedback.get("issues", [])
            context.execution_results["requires_rollback"] = feedback.get("rollback", False)

    async def _handle_review_feedback(self, 
                                    context: WorkflowContext, 
                                    feedback: Dict):
        """
        Processes final review feedback and prepares for workflow completion
        """
        context.execution_results["final_feedback"] = feedback
        context.execution_results["success_rating"] = feedback.get("success_rating", 0.0)

    async def _start_planning(self, context: WorkflowContext):
        """
        Initiates the planning phase using HRM or fallback
        """
        # Create appropriate agent for planning
        agent = self.agent_factory.create_agent(
            user_request=context.interpretation.interpreted_intent,
            user_context={"workflow_id": context.session_id}
        )
        
        # Initialize agent runtime
        runtime = AgentRuntime(agent)
        
        # Generate plan
        context.plan = await runtime.generate_plan(context.interpretation)
        
        # Record in session memory
        self.memory_manager.record_step(context.session_id, {
            "state": context.current_state.value,
            "plan": context.plan
        })

    def _requires_plan_clarification(self, context: WorkflowContext) -> bool:
        """
        Determines if the current plan needs clarification
        """
        if not context.plan:
            return True
        return context.plan.get("confidence_score", 0.0) < 0.85

    async def _start_execution(self, context: WorkflowContext):
        """
        Begins execution of the approved plan
        """
        agent = self.agent_factory.create_agent(
            user_request=context.interpretation.interpreted_intent,
            user_context={"workflow_id": context.session_id}
        )
        
        runtime = AgentRuntime(agent)
        
        # Execute plan
        context.execution_results = await runtime.execute_plan(context.plan)
        
        # Record in session memory
        self.memory_manager.record_step(context.session_id, {
            "state": context.current_state.value,
            "execution_results": context.execution_results
        })

    async def _complete_workflow(self, context: WorkflowContext):
        """
        Finalizes workflow and commits to permanent memory
        """
        # Commit session to permanent memory
        self.memory_manager.commit_session(context.session_id)
        
        # Cleanup
        del self.active_workflows[context.session_id]
