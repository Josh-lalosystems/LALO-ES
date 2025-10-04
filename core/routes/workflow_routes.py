"""
LALO Workflow API Routes

Implements the 5-step LALO workflow process:
1. Semantic Interpretation & Confidence Scoring
2. Planning
3. Backup & Execution
4. Review
5. Final Feedback & Permanent Memory Commit
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime
from uuid import uuid4
import json
import os

from ..database import WorkflowSession, WorkflowState, SessionLocal
from ..services.auth import get_current_user
from ..services.ai_service import ai_service
from ..services.key_management import key_manager
from ..services.workflow_orchestrator import workflow_orchestrator

router = APIRouter(prefix="/api/workflow", tags=["LALO Workflow"])

# Autonomy / auto-approval mode
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"
# If AUTO_APPROVE is not explicitly set, default to True in DEMO_MODE; otherwise False
AUTO_APPROVE = os.getenv("AUTO_APPROVE", "true" if DEMO_MODE else "false").lower() == "true"

# ============================================================================
# Request/Response Models
# ============================================================================

class StartWorkflowRequest(BaseModel):
    user_request: str
    prebuilt_workflow_id: Optional[str] = None

class FeedbackRequest(BaseModel):
    feedback_type: str  # "approve", "reject", "clarify"
    message: Optional[str] = None
    clarifications: Optional[Dict] = None

class WorkflowStatusResponse(BaseModel):
    session_id: str
    current_state: str
    original_request: str
    created_at: str
    updated_at: str

    # Step 1: Interpretation
    interpreted_intent: Optional[str] = None
    confidence_score: Optional[float] = None
    reasoning_trace: Optional[List[str]] = None
    suggested_clarifications: Optional[List[str]] = None
    interpretation_approved: Optional[int] = None

    # Step 2: Planning
    action_plan: Optional[Dict] = None
    plan_confidence_score: Optional[float] = None
    plan_approved: Optional[int] = None

    # Step 3: Execution
    execution_results: Optional[Dict] = None
    execution_steps_log: Optional[List] = None
    execution_success: Optional[int] = None

    # Step 4/5: Review
    review_feedback: Optional[Dict] = None
    final_feedback: Optional[str] = None
    success_rating: Optional[float] = None

    # Feedback history
    feedback_history: Optional[List] = None

    # Error
    error_message: Optional[str] = None

class AutoApproveStatus(BaseModel):
    auto_approve: bool

@router.get("/auto_approve", response_model=AutoApproveStatus)
async def get_auto_approve_status() -> AutoApproveStatus:
    return AutoApproveStatus(auto_approve=AUTO_APPROVE)

@router.post("/auto_approve/{enabled}", response_model=AutoApproveStatus)
async def set_auto_approve(enabled: bool, current_user: str = Depends(get_current_user)) -> AutoApproveStatus:
    """
    Toggle auto-approval at runtime (process-level). Intended for dev/demo; for production use env vars.
    Note: This sets a module-level flag and affects new requests immediately.
    """
    global AUTO_APPROVE
    AUTO_APPROVE = bool(enabled)
    return AutoApproveStatus(auto_approve=AUTO_APPROVE)

# ============================================================================
# Workflow Endpoints
# ============================================================================

@router.post("/start")
async def start_workflow(
    request: StartWorkflowRequest,
    current_user: str = Depends(get_current_user)
) -> WorkflowStatusResponse:
    """
    Step 1: Start a new LALO workflow
    - Creates session
    - Performs semantic interpretation
    - Generates confidence score
    - Returns interpretation for user approval
    """
    try:
        # Ensure user has API keys and models initialized
        api_keys = key_manager.get_keys(current_user)
        if not api_keys:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No API keys configured. Please add API keys in Settings before starting a workflow."
            )

        # Validate which keys are working
        key_status = await key_manager.validate_keys(current_user)

        # Check if we have at least OpenAI working
        if not key_status.get("openai", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OpenAI API key is not working. Please check your API key in Settings."
            )

        # Initialize user models if needed (only for working keys)
        if current_user not in ai_service.models:
            ai_service.initialize_user_models(current_user, api_keys, key_status)

        # Use workflow orchestrator to start workflow
        session_dict = await workflow_orchestrator.start_workflow(
            user_request=request.user_request,
            user_id=current_user,
            context={"auto_approve": AUTO_APPROVE}
        )

        # Convert to response model
        return WorkflowStatusResponse(**session_dict)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start workflow: {str(e)}"
        )


@router.get("/{session_id}/status")
async def get_workflow_status(
    session_id: str,
    current_user: str = Depends(get_current_user)
) -> WorkflowStatusResponse:
    """Get current status of a workflow session"""
    try:
        session_dict = await workflow_orchestrator.get_workflow_status(
            session_id=session_id,
            user_id=current_user
        )

        if not session_dict:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow session {session_id} not found"
            )

        return WorkflowStatusResponse(**session_dict)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get workflow status: {str(e)}"
        )


@router.post("/{session_id}/approve_interpretation")
async def approve_interpretation(
    session_id: str,
    current_user: str = Depends(get_current_user),
    feedback: Optional[str] = None
) -> WorkflowStatusResponse:
    """Approve interpretation and proceed to planning"""
    try:
        session_dict = await workflow_orchestrator.approve_interpretation(
            session_id=session_id,
            user_id=current_user,
            feedback=feedback
        )
        return WorkflowStatusResponse(**session_dict)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve interpretation: {str(e)}"
        )

@router.post("/{session_id}/approve_plan")
async def approve_plan(
    session_id: str,
    current_user: str = Depends(get_current_user),
    feedback: Optional[str] = None
) -> WorkflowStatusResponse:
    """Approve action plan and proceed to execution"""
    try:
        session_dict = await workflow_orchestrator.approve_plan(
            session_id=session_id,
            user_id=current_user,
            feedback=feedback
        )
        return WorkflowStatusResponse(**session_dict)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve plan: {str(e)}"
        )

@router.post("/{session_id}/approve_results")
async def approve_results(
    session_id: str,
    current_user: str = Depends(get_current_user),
    feedback: Optional[str] = None,
    rating: Optional[float] = None
) -> WorkflowStatusResponse:
    """Approve execution results and finalize workflow"""
    try:
        session_dict = await workflow_orchestrator.approve_results(
            session_id=session_id,
            user_id=current_user,
            feedback=feedback,
            rating=rating
        )
        return WorkflowStatusResponse(**session_dict)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve results: {str(e)}"
        )

@router.post("/{session_id}/reject")
async def reject_step(
    session_id: str,
    current_user: str = Depends(get_current_user),
    reason: Optional[str] = None
) -> WorkflowStatusResponse:
    """Reject current step and mark workflow as error"""
    try:
        session_dict = await workflow_orchestrator.reject_step(
            session_id=session_id,
            user_id=current_user,
            reason=reason
        )
        return WorkflowStatusResponse(**session_dict)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reject step: {str(e)}"
        )

@router.get("/sessions")
async def list_workflow_sessions(
    current_user: str = Depends(get_current_user),
    limit: int = 20,
    offset: int = 0
) -> List[WorkflowStatusResponse]:
    """List all workflow sessions for current user"""
    try:
        sessions_list = await workflow_orchestrator.list_sessions(
            user_id=current_user,
            limit=limit,
            offset=offset
        )
        return [WorkflowStatusResponse(**session) for session in sessions_list]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list sessions: {str(e)}"
        )
