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
Agent Management API Routes

Provides endpoints for creating, managing, and executing custom AI agents
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from core.services.agent_manager import agent_manager
from core.services.agent_engine import agent_engine
from core.services.auth import get_current_user
from core.validators import validate_agent_config
from core.services.agent_runtime import runtime_agent_manager
from core.services.workflow_state import workflow_manager
from core.services.agent_orchestrator_runtime import agent_orchestrator
from core.services.rbac_dependency import require_permission
from pydantic import BaseModel


class CreateRuntimeAgentRequest(BaseModel):
    agent_type: str
    config: Optional[Dict[str, Any]] = None


class AssignTaskRequest(BaseModel):
    task: Dict[str, Any]


class CreateWorkflowRequest(BaseModel):
    name: str
    steps: List[Dict[str, Any]]

router = APIRouter(prefix="/api", tags=["agents"])


# Request/Response Models
class AgentCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    category: Optional[str] = "general"
    system_prompt: str = Field(..., min_length=1)
    model: str = "gpt-3.5-turbo"
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2000, ge=1, le=100000)
    top_p: Optional[float] = Field(default=1.0, ge=0.0, le=1.0)
    frequency_penalty: Optional[float] = Field(default=0, ge=-2.0, le=2.0)
    presence_penalty: Optional[float] = Field(default=0, ge=-2.0, le=2.0)
    allowed_tools: List[str] = Field(default_factory=list)
    required_permissions: List[str] = Field(default_factory=list)
    guardrails: List[Dict[str, Any]] = Field(default_factory=list)
    max_iterations: int = Field(default=10, ge=1, le=100)
    timeout_seconds: int = Field(default=300, ge=1, le=3600)
    tags: List[str] = Field(default_factory=list)
    icon: Optional[str] = "🤖"
    color: Optional[str] = "#1976d2"


class AgentUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    system_prompt: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    allowed_tools: Optional[List[str]] = None
    required_permissions: Optional[List[str]] = None
    guardrails: Optional[List[Dict[str, Any]]] = None
    max_iterations: Optional[int] = None
    timeout_seconds: Optional[int] = None
    tags: Optional[List[str]] = None
    icon: Optional[str] = None
    color: Optional[str] = None


class AgentExecuteRequest(BaseModel):
    user_input: str = Field(..., min_length=1)
    context: Optional[Dict[str, Any]] = None


class AgentRateRequest(BaseModel):
    rating: float = Field(..., ge=1.0, le=5.0)
    review: Optional[str] = None


class AgentCloneRequest(BaseModel):
    new_name: Optional[str] = None


# Agent Management Endpoints

@router.post("/agents")
async def create_agent(
    agent_data: AgentCreateRequest,
    current_user: str = Depends(get_current_user)
):
    """Create a new custom agent"""
    try:
        # Validate agent configuration
        validated_data = validate_agent_config(agent_data.dict())

        # Create agent
        agent = agent_manager.create_agent(current_user, validated_data)

        return agent
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create agent: {str(e)}"
        )


@router.get("/agents")
async def list_agents(current_user: str = Depends(get_current_user)):
    """List all agents created by the current user"""
    try:
        agents = agent_manager.list_user_agents(current_user)
        return agents
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list agents: {str(e)}"
        )


@router.get("/agents/{agent_id}")
async def get_agent(
    agent_id: str,
    current_user: str = Depends(get_current_user)
):
    """Get a specific agent by ID"""
    try:
        agent = agent_manager.get_agent(agent_id, current_user)

        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found or access denied"
            )

        return agent
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get agent: {str(e)}"
        )


@router.put("/agents/{agent_id}")
async def update_agent(
    agent_id: str,
    updates: AgentUpdateRequest,
    current_user: str = Depends(get_current_user)
):
    """Update an existing agent"""
    try:
        # Filter out None values
        update_data = {k: v for k, v in updates.dict().items() if v is not None}

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No updates provided"
            )

        # Update agent
        agent = agent_manager.update_agent(agent_id, current_user, update_data)

        return agent
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update agent: {str(e)}"
        )


@router.delete("/agents/{agent_id}")
async def delete_agent(
    agent_id: str,
    current_user: str = Depends(get_current_user)
):
    """Delete an agent"""
    try:
        success = agent_manager.delete_agent(agent_id, current_user)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found or access denied"
            )

        return {"success": True, "message": "Agent deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete agent: {str(e)}"
        )


@router.post("/agents/{agent_id}/clone")
async def clone_agent(
    agent_id: str,
    request: AgentCloneRequest,
    current_user: str = Depends(get_current_user)
):
    """Clone an existing agent"""
    try:
        agent = agent_manager.clone_agent(agent_id, current_user, request.new_name)
        return agent
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clone agent: {str(e)}"
        )


# Agent Execution

@router.post("/agents/{agent_id}/execute")
async def execute_agent(
    agent_id: str,
    request: AgentExecuteRequest,
    current_user: str = Depends(get_current_user)
):
    """Execute an agent with user input"""
    try:
        result = await agent_engine.execute_agent(
            agent_id=agent_id,
            user_id=current_user,
            user_input=request.user_input,
            context=request.context
        )

        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute agent: {str(e)}"
        )


# -------------------------
# Runtime (ephemeral) agents
# -------------------------


@router.post("/runtime/agents/create")
async def create_runtime_agent(
    payload: CreateRuntimeAgentRequest,
    current_user: str = Depends(get_current_user),
    _perm: bool = Depends(require_permission("agent.manage"))
):
    """Create an ephemeral runtime agent (in-memory)"""
    agent_id = runtime_agent_manager.create_agent(payload.agent_type, payload.config or {})
    return {"agent_id": agent_id, "type": payload.agent_type}


@router.get("/runtime/agents/list")
async def list_runtime_agents(
    current_user: str = Depends(get_current_user),
    _perm: bool = Depends(require_permission("agent.manage"))
):
    return {"agents": [runtime_agent_manager.get_agent_status(aid) for aid in runtime_agent_manager.agents.keys()]}


@router.get("/runtime/agents/{agent_id}/status")
async def get_runtime_agent_status(
    agent_id: str,
    current_user: str = Depends(get_current_user),
    _perm: bool = Depends(require_permission("agent.manage"))
):
    return runtime_agent_manager.get_agent_status(agent_id)


@router.post("/runtime/agents/{agent_id}/assign")
async def assign_task_to_runtime_agent(
    agent_id: str,
    payload: AssignTaskRequest,
    current_user: str = Depends(get_current_user),
    _perm: bool = Depends(require_permission("agent.assign"))
):
    """Assign a task to a specific runtime agent (in-memory)."""
    if agent_id not in runtime_agent_manager.agents:
        raise HTTPException(status_code=404, detail="Agent not found")

    agent = runtime_agent_manager.agents[agent_id]

    # Basic validation: ensure prompt present (required for model execution)
    if not payload.task or not isinstance(payload.task, dict) or not payload.task.get("prompt"):
        raise HTTPException(status_code=400, detail="Task must include a 'prompt' field for execution")

    task_id = agent.assign_task(payload.task)
    return {"agent_id": agent_id, "task_id": task_id}


@router.post("/runtime/agents/assign")
async def assign_task_via_orchestrator(
    agent_type: str,
    payload: AssignTaskRequest,
    current_user: str = Depends(get_current_user),
    _perm: bool = Depends(require_permission("agent.assign"))
):
    """Assign a task via the orchestrator to an agent of the given type."""
    # Basic validation: ensure prompt present
    if not payload.task or not isinstance(payload.task, dict) or not payload.task.get("prompt"):
        raise HTTPException(status_code=400, detail="Task must include a 'prompt' field for execution")

    agent_id, task_id = agent_orchestrator.assign_task(agent_type, payload.task)
    return {"agent_id": agent_id, "task_id": task_id}


# -------------------------
# Workflow endpoints
# -------------------------


@router.post("/runtime/workflows/create")
async def create_workflow(
    payload: CreateWorkflowRequest,
    current_user: str = Depends(get_current_user),
    _perm: bool = Depends(require_permission("agent.manage"))
):
    # Require manage permission to create workflows
    # (permission enforced by route dependency)
    workflow_id = workflow_manager.create_workflow(payload.name, payload.steps)
    return {"workflow_id": workflow_id, "name": payload.name}


@router.post("/runtime/workflows/{workflow_id}/start")
async def start_workflow(
    workflow_id: str,
    current_user: str = Depends(get_current_user),
    _perm: bool = Depends(require_permission("workflow.start"))
):
    """Start a workflow execution (pure state machine)."""
    workflow_manager.start_workflow(workflow_id)
    return {"workflow_id": workflow_id, "status": "started"}


@router.get("/runtime/workflows/{workflow_id}/status")
async def get_workflow_status(
    workflow_id: str,
    current_user: str = Depends(get_current_user),
    _perm: bool = Depends(require_permission("agent.manage"))
):
    return workflow_manager.get_workflow_status(workflow_id)


# Marketplace Endpoints

@router.get("/marketplace")
async def list_public_agents(
    category: Optional[str] = None,
    tags: Optional[str] = None
):
    """List public agents in the marketplace"""
    try:
        tag_list = tags.split(',') if tags else None
        agents = agent_manager.list_public_agents(category=category, tags=tag_list)
        return agents
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list marketplace agents: {str(e)}"
        )


@router.get("/marketplace/{agent_id}")
async def get_public_agent(agent_id: str):
    """Get a specific public agent from the marketplace"""
    try:
        agent = agent_manager.get_agent(agent_id)

        if not agent or not agent.is_public:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found in marketplace"
            )

        return agent
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get marketplace agent: {str(e)}"
        )


@router.post("/agents/{agent_id}/publish")
async def publish_agent(
    agent_id: str,
    current_user: str = Depends(get_current_user)
):
    """Publish an agent to the marketplace"""
    try:
        agent = agent_manager.publish_agent(agent_id, current_user)
        return agent
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to publish agent: {str(e)}"
        )


@router.post("/agents/{agent_id}/rate")
async def rate_agent(
    agent_id: str,
    request: AgentRateRequest,
    current_user: str = Depends(get_current_user)
):
    """Rate an agent"""
    try:
        agent_manager.rate_agent(
            agent_id=agent_id,
            user_id=current_user,
            rating=request.rating,
            review=request.review
        )

        return {"success": True, "message": "Rating submitted successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to rate agent: {str(e)}"
        )
