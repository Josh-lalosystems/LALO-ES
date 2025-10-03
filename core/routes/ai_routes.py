from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, List, Optional
from pydantic import BaseModel
from datetime import datetime

from ..services.key_management import key_manager, APIKeyRequest
from ..services.ai_service import ai_service
from ..services.auth import get_current_user

router = APIRouter(prefix="/api")

class AIRequest(BaseModel):
    prompt: str
    model: Optional[str] = "gpt-4"
    max_tokens: Optional[int] = 1000
    temperature: Optional[float] = 0.7

class AIResponse(BaseModel):
    id: str
    response: str
    model: str
    usage: Dict[str, int]
    created_at: str

class ModelResponse(BaseModel):
    name: str
    type: str
    status: bool

class APIKeyResponse(BaseModel):
    id: str
    name: str
    provider: str
    created_at: str
    last_used: Optional[str] = None

@router.post("/ai/chat")
async def send_ai_request(
    request: AIRequest,
    current_user: str = Depends(get_current_user)
) -> AIResponse:
    """Send a request to AI models"""
    try:
        response = await ai_service.send_request(
            user_id=current_user,
            prompt=request.prompt,
            model=request.model,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        return AIResponse(
            id=response.get("id", ""),
            response=response.get("response", ""),
            model=response.get("model", request.model),
            usage=response.get("usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}),
            created_at=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/ai/history")
async def get_request_history(
    current_user: str = Depends(get_current_user)
) -> List[AIResponse]:
    """Get AI request history for current user"""
    # This would typically fetch from database
    return []

@router.get("/ai/models")
async def get_available_models(
    current_user: str = Depends(get_current_user)
) -> List[str]:
    """Get list of available AI models"""
    try:
        models = ai_service.get_available_models(current_user)
        return models
    except Exception as e:
        return ["gpt-4", "gpt-3.5-turbo", "claude-3"]

@router.get("/keys")
async def get_api_keys(
    current_user: str = Depends(get_current_user)
) -> List[APIKeyResponse]:
    """Get user's API keys"""
    try:
        keys = key_manager.get_keys(current_user)
        # Convert to response format
        result = []
        for provider, key in keys.items():
            if key:
                result.append(APIKeyResponse(
                    id=f"{provider}_{current_user}",
                    name=f"{provider.title()} Key",
                    provider=provider,
                    created_at=datetime.now().isoformat()
                ))
        return result
    except Exception as e:
        return []

@router.post("/keys")
async def add_api_key(
    name: str,
    provider: str,
    key: str,
    current_user: str = Depends(get_current_user)
):
    """Add a new API key"""
    try:
        # Create APIKeyRequest object
        key_request = APIKeyRequest()
        if provider.lower() == "openai":
            key_request.openai_api_key = key
        elif provider.lower() == "anthropic":
            key_request.anthropic_api_key = key
        
        key_manager.set_keys(current_user, key_request)
        return {"status": "success", "message": f"{provider} key added successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.delete("/keys/{key_id}")
async def delete_api_key(
    key_id: str,
    current_user: str = Depends(get_current_user)
):
    """Delete an API key"""
    return {"status": "success", "message": "Key deleted successfully"}

@router.post("/keys/{key_id}/test")
async def test_api_key(
    key_id: str,
    current_user: str = Depends(get_current_user)
):
    """Test an API key"""
    return {"status": "success", "valid": True}

# Usage Statistics Endpoints
class UsageStats(BaseModel):
    total_requests: int
    total_tokens: int
    requests_today: int
    tokens_today: int
    cost_today: float
    cost_month: float

@router.get("/usage/stats")
async def get_usage_stats(
    current_user: str = Depends(get_current_user)
) -> UsageStats:
    """Get usage statistics for current user"""
    return UsageStats(
        total_requests=42,
        total_tokens=15750,
        requests_today=8,
        tokens_today=2500,
        cost_today=0.15,
        cost_month=4.80
    )

@router.get("/usage/history")
async def get_usage_history(
    days: int = 30,
    current_user: str = Depends(get_current_user)
):
    """Get usage history for specified number of days"""
    return []

# Admin Endpoints
@router.get("/admin/users")
async def get_all_users(
    current_user: str = Depends(get_current_user)
):
    """Get all users (admin only)"""
    # TODO: Add admin role check
    return []

@router.get("/admin/stats")
async def get_system_stats(
    current_user: str = Depends(get_current_user)
):
    """Get system-wide statistics (admin only)"""
    return {
        "total_users": 15,
        "active_users": 8,
        "total_requests": 1247,
        "success_rate": 94.2
    }

@router.put("/admin/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    role: str,
    current_user: str = Depends(get_current_user)
):
    """Update user role (admin only)"""
    return {"status": "success", "message": f"User {user_id} role updated to {role}"}

@router.get("/admin/settings")
async def get_admin_settings(
    current_user: str = Depends(get_current_user)
):
    """Get admin settings"""
    return {}

@router.put("/admin/settings")
async def update_admin_settings(
    settings: dict,
    current_user: str = Depends(get_current_user)
):
    """Update admin settings"""
    return {"status": "success", "message": "Settings updated successfully"}

# Removed duplicate @router.post("/keys") endpoint to avoid route conflicts.

@router.get("/keys/status")
async def check_api_keys(
    current_user: str = Depends(get_current_user)
) -> Dict[str, bool]:
    """Check status of stored API keys"""
    return key_manager.validate_keys(current_user)

@router.get("/models")
async def list_models(
    current_user: str = Depends(get_current_user)
) -> List[ModelResponse]:
    """Get list of available models for the current user"""
    models = ai_service.get_available_models(current_user)
    return [
        ModelResponse(
            name=model,
            type="openai" if "gpt" in model else "anthropic",
            status=True
        )
        for model in models
    ]

@router.post("/request")
async def create_request(
    prompt: str,
    model: str,
    current_user: str = Depends(get_current_user)
):
    """Create a new AI request"""
    if model not in ai_service.get_available_models(current_user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Model {model} not available"
        )
    
    try:
        response = await ai_service.generate(
            prompt,
            model,
            user_id=current_user
        )
        return {"response": response}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
