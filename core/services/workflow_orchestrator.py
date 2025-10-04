# Copyright (c) 2025 LALO AI LLC. All rights reserved.
"""
Workflow Orchestrator - The Heart of LALO

Coordinates the complete 5-step LALO workflow:
1. Semantic Interpretation (with confidence scoring)
2. Action Planning (with recursive refinement)
3. Execution (with backup and verification)
4. Review (human feedback)
5. Commit (to permanent memory)

This is the main orchestration engine that brings everything together.
"""

from typing import Dict, Any, Optional, Callable
from datetime import datetime
from core.database import SessionLocal, WorkflowSession, WorkflowState, FeedbackEvent
from core.services.semantic_interpreter import semantic_interpreter
from core.services.action_planner import action_planner
from core.services.tool_executor import tool_executor
from dataclasses import asdict
import logging
import uuid
import json

logger = logging.getLogger(__name__)


class WorkflowOrchestrator:
    """
    Orchestrates the complete LALO workflow with human-in-the-loop

    The workflow:
    1. INTERPRETING: User request → Semantic interpretation + confidence
    2. PLANNING: Interpreted intent → Action plan with self-critique
    3. EXECUTING: Action plan → Tool execution with verification
    4. REVIEWING: Results → Human review and feedback
    5. FINALIZING: Approved results → Commit to permanent memory
    """

    def __init__(self):
        """Initialize workflow orchestrator"""
        self.active_workflows = {}  # session_id → workflow state

    async def start_workflow(
        self,
        user_request: str,
        user_id: str,
        context: Dict = None
    ) -> Dict:
        """
        Start a new LALO workflow

        Args:
            user_request: The user's original request
            user_id: User ID
            context: Optional context (conversation history, etc.)

        Returns:
            Dict with workflow session info and initial state
        """
        session_id = str(uuid.uuid4())
        logger.info(f"Starting workflow {session_id} for user {user_id}")

        # Create workflow session in database
        db = SessionLocal()
        try:
            session = WorkflowSession(
                session_id=session_id,
                user_id=user_id,
                current_state=WorkflowState.INTERPRETING,
                original_request=user_request,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(session)
            db.commit()
            db.refresh(session)

            # Store in active workflows
            self.active_workflows[session_id] = {
                "session": session,
                "callbacks": {}
            }

            # Start Step 1: Semantic Interpretation
            await self._run_interpretation(session_id, user_id)

            # Get updated session
            db.refresh(session)

            return self._session_to_dict(session)

        finally:
            db.close()

    async def _run_interpretation(self, session_id: str, user_id: str):
        """
        Step 1: Semantic Interpretation

        - Extract intent from user request
        - Score confidence
        - Generate clarifications if needed
        """
        db = SessionLocal()
        try:
            session = db.query(WorkflowSession).filter(
                WorkflowSession.session_id == session_id
            ).first()

            if not session:
                logger.error(f"Session {session_id} not found")
                return

            logger.info(f"Running interpretation for workflow {session_id}")

            # Run semantic interpretation
            result = await semantic_interpreter.interpret(
                user_request=session.original_request,
                user_id=user_id
            )

            # Update session with interpretation results
            session.interpreted_intent = result.interpreted_intent
            session.confidence_score = result.confidence_score
            session.reasoning_trace = result.reasoning_trace
            session.suggested_clarifications = result.suggested_clarifications
            session.updated_at = datetime.utcnow()

            # Determine next state
            if result.feedback_required:
                # Need clarification - wait for human feedback
                session.current_state = WorkflowState.INTERPRETING
                session.interpretation_approved = 0  # Pending
                logger.info("Interpretation requires clarification")
            else:
                # Auto-approve high confidence interpretations
                session.interpretation_approved = 1
                session.current_state = WorkflowState.PLANNING
                logger.info("Interpretation approved, moving to planning")

                # Immediately start planning
                db.commit()
                await self._run_planning(session_id, user_id)
                return  # Return early as state already updated

            db.commit()

        finally:
            db.close()

    async def approve_interpretation(
        self,
        session_id: str,
        user_id: str,
        feedback: str = None
    ):
        """
        Human approves interpretation or provides clarification

        Args:
            session_id: Workflow session ID
            user_id: User ID
            feedback: Optional clarification feedback
        """
        db = SessionLocal()
        try:
            session = db.query(WorkflowSession).filter(
                WorkflowSession.session_id == session_id
            ).first()

            if feedback:
                # User provided clarification - refine interpretation
                logger.info(f"Refining interpretation with user feedback for {session_id}")

                result = await semantic_interpreter.refine_with_feedback(
                    original_request=session.original_request,
                    user_feedback=feedback,
                    user_id=user_id
                )

                session.interpreted_intent = result.interpreted_intent
                session.confidence_score = result.confidence_score
                session.reasoning_trace = result.reasoning_trace

            # Mark as approved
            session.interpretation_approved = 1
            session.current_state = WorkflowState.PLANNING
            session.updated_at = datetime.utcnow()

            # Record feedback event
            self._record_feedback(
                db=db,
                session_id=session_id,
                user_id=user_id,
                step="interpretation",
                feedback_type="approve",
                feedback_value=feedback
            )

            db.commit()

            # Move to next step: Planning
            await self._run_planning(session_id, user_id)

        finally:
            db.close()

    async def _run_planning(self, session_id: str, user_id: str):
        """
        Step 2: Action Planning

        - Generate action plan
        - Self-critique and refine
        - Iterate until confidence threshold met
        """
        db = SessionLocal()
        try:
            session = db.query(WorkflowSession).filter(
                WorkflowSession.session_id == session_id
            ).first()

            logger.info(f"Running planning for workflow {session_id}")

            # Create action plan
            plan = await action_planner.create_plan(
                interpreted_intent=session.interpreted_intent,
                user_id=user_id
            )

            # Update session with plan
            session.action_plan = {
                "steps": plan.steps,
                "retrieved_examples": plan.retrieved_examples,
                "iterations": plan.iterations,
                "critiques": plan.critiques
            }
            session.plan_confidence_score = plan.confidence
            session.updated_at = datetime.utcnow()

            # Determine if plan needs approval
            if plan.confidence >= 0.85:
                # High confidence - auto-approve
                session.plan_approved = 1
                session.current_state = WorkflowState.BACKUP_VERIFY
                logger.info("Plan auto-approved, moving to execution")

                db.commit()
                # Start execution
                await self._run_execution(session_id, user_id)
                return

            else:
                # Lower confidence - request human approval
                session.plan_approved = 0
                session.current_state = WorkflowState.PLANNING
                logger.info("Plan requires human approval")

            db.commit()

        finally:
            db.close()

    async def approve_plan(self, session_id: str, user_id: str, feedback: str = None):
        """
        Human approves action plan

        Args:
            session_id: Workflow session ID
            user_id: User ID
            feedback: Optional feedback on plan
        """
        db = SessionLocal()
        try:
            session = db.query(WorkflowSession).filter(
                WorkflowSession.session_id == session_id
            ).first()

            # Mark plan as approved
            session.plan_approved = 1
            session.current_state = WorkflowState.BACKUP_VERIFY
            session.updated_at = datetime.utcnow()

            # Record feedback
            self._record_feedback(
                db=db,
                session_id=session_id,
                user_id=user_id,
                step="planning",
                feedback_type="approve",
                feedback_value=feedback
            )

            db.commit()

            # Start execution
            await self._run_execution(session_id, user_id)

        finally:
            db.close()

    async def _run_execution(self, session_id: str, user_id: str):
        """
        Step 3: Execution

        - Create backup
        - Execute plan step by step
        - Verify results
        - Rollback on failure
        """
        db = SessionLocal()
        try:
            session = db.query(WorkflowSession).filter(
                WorkflowSession.session_id == session_id
            ).first()

            logger.info(f"Running execution for workflow {session_id}")

            # Transition to executing state
            session.current_state = WorkflowState.EXECUTING
            session.updated_at = datetime.utcnow()
            db.commit()

            # Parse action plan
            from core.services.action_planner import ActionPlan
            from dataclasses import dataclass

            # Reconstruct ActionPlan from stored data
            plan_data = session.action_plan
            plan = ActionPlan(
                steps=plan_data.get("steps", []),
                confidence=session.plan_confidence_score or 0.5,
                iterations=plan_data.get("iterations", 1),
                critiques=plan_data.get("critiques", []),
                retrieved_examples=plan_data.get("retrieved_examples", []),
                metadata={}
            )

            # Execute plan
            results = await tool_executor.execute_plan(
                action_plan=plan,
                user_id=user_id,
                workflow_session_id=session_id,
                human_approval=True
            )

            # Update session with results
            session.execution_results = {
                "steps": [
                    {
                        "step": r.step_number,
                        "success": r.success,
                        "tool": r.tool_name,
                        "output": str(r.tool_output) if r.tool_output else None,
                        "error": r.error
                    }
                    for r in results
                ]
            }

            session.execution_steps_log = [
                {
                    "step": r.step_number,
                    "status": "success" if r.success else "failed",
                    "backup_restored": r.backup_restored
                }
                for r in results
            ]

            # Determine overall success
            all_success = all(r.success for r in results)
            session.execution_success = 1 if all_success else 0

            # Move to review
            session.current_state = WorkflowState.REVIEWING
            session.updated_at = datetime.utcnow()

            logger.info(f"Execution {'succeeded' if all_success else 'failed'}")

            db.commit()

        finally:
            db.close()

    async def approve_results(
        self,
        session_id: str,
        user_id: str,
        rating: float = None,
        feedback: str = None
    ):
        """
        Human approves final results

        Args:
            session_id: Workflow session ID
            user_id: User ID
            rating: Quality rating (0.0-1.0)
            feedback: Final feedback
        """
        db = SessionLocal()
        try:
            session = db.query(WorkflowSession).filter(
                WorkflowSession.session_id == session_id
            ).first()

            # Mark as approved
            session.review_approved = 1
            session.final_feedback = feedback
            session.success_rating = rating
            session.current_state = WorkflowState.FINALIZING
            session.updated_at = datetime.utcnow()

            # Record feedback
            self._record_feedback(
                db=db,
                session_id=session_id,
                user_id=user_id,
                step="review",
                feedback_type="approve",
                rating=rating,
                comments=feedback
            )

            db.commit()

            # Commit to permanent memory
            await self._commit_to_memory(session_id, user_id)

        finally:
            db.close()

    async def _commit_to_memory(self, session_id: str, user_id: str):
        """
        Step 5: Commit to Permanent Memory

        Save successful workflow for future learning
        """
        db = SessionLocal()
        try:
            session = db.query(WorkflowSession).filter(
                WorkflowSession.session_id == session_id
            ).first()

            logger.info(f"Committing workflow {session_id} to permanent memory")

            # Mark as committed
            session.committed_to_permanent_memory = 1
            session.current_state = WorkflowState.COMPLETED
            session.completed_at = datetime.utcnow()
            session.updated_at = datetime.utcnow()

            # TODO: Actual memory storage
            # In production:
            # - Store in vector database for RAG
            # - Update RTI examples
            # - Fine-tune models with feedback

            db.commit()

            logger.info(f"Workflow {session_id} completed successfully")

        finally:
            db.close()

    def _record_feedback(
        self,
        db,
        session_id: str,
        user_id: str,
        step: str,
        feedback_type: str,
        feedback_value: str = None,
        rating: float = None,
        comments: str = None
    ):
        """
        Record feedback event in database

        Args:
            db: Database session
            session_id: Workflow session ID
            user_id: User ID
            step: Workflow step (interpretation, planning, review)
            feedback_type: Type of feedback (approve, reject, clarify)
            feedback_value: Feedback value
            rating: Numerical rating
            comments: Free-text comments
        """
        feedback_event = FeedbackEvent(
            id=str(uuid.uuid4()),
            workflow_session_id=session_id,
            user_id=user_id,
            step=step,
            feedback_type=feedback_type,
            feedback_value=feedback_value,
            rating=rating,
            comments=comments,
            created_at=datetime.utcnow()
        )
        db.add(feedback_event)

    def _session_to_dict(self, session: WorkflowSession) -> Dict:
        """Convert WorkflowSession to dictionary"""
        return {
            "session_id": session.session_id,
            "user_id": session.user_id,
            "current_state": session.current_state.value if session.current_state else None,
            "original_request": session.original_request,
            "interpreted_intent": session.interpreted_intent,
            "confidence_score": session.confidence_score,
            "reasoning_trace": session.reasoning_trace,
            "suggested_clarifications": session.suggested_clarifications,
            "interpretation_approved": session.interpretation_approved,
            "action_plan": session.action_plan,
            "plan_confidence_score": session.plan_confidence_score,
            "plan_approved": session.plan_approved,
            "execution_results": session.execution_results,
            "execution_success": session.execution_success,
            "review_approved": session.review_approved,
            "final_feedback": session.final_feedback,
            "success_rating": session.success_rating,
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "updated_at": session.updated_at.isoformat() if session.updated_at else None,
            "completed_at": session.completed_at.isoformat() if session.completed_at else None
        }

    async def get_workflow_status(self, session_id: str) -> Dict:
        """
        Get current workflow status

        Args:
            session_id: Workflow session ID

        Returns:
            Dict with current workflow state
        """
        db = SessionLocal()
        try:
            session = db.query(WorkflowSession).filter(
                WorkflowSession.session_id == session_id
            ).first()

            if not session:
                return {"error": "Workflow not found"}

            return self._session_to_dict(session)

        finally:
            db.close()


# Global workflow orchestrator instance
workflow_orchestrator = WorkflowOrchestrator()
