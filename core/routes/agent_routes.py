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
