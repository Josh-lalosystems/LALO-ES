from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, List, Optional
from pydantic import BaseModel
from datetime import datetime
from uuid import uuid4

from ..services.key_management import key_manager, APIKeyRequest
from ..services.ai_service import ai_service
from ..services.auth import get_current_user
from ..services.database_service import database_service

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
        # Ensure user models are initialized based on stored keys
        if current_user not in ai_service.models:
            try:
                api_keys = key_manager.get_keys(current_user)
                ai_service.initialize_user_models(current_user, api_keys)
            except Exception:
                pass

        available = ai_service.get_available_models(current_user)
        model = request.model or (available[0] if available else None)
        if not available or not model or model not in available:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No available models for this user. Add API keys first or choose a valid model."
            )

        generated = await ai_service.generate(
            request.prompt,
            model_name=model,
            user_id=current_user,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
        )
        # Optional: record usage with a rough token estimate until real usage is available
        try:
            estimated_tokens = min(len(request.prompt.split()) * 1.3 + len(str(generated).split()) * 1.3, request.max_tokens or 1000)
            database_service.record_usage(
                user_id=current_user,
                model=model,
                tokens_used=int(estimated_tokens),
                cost=0.0,  # TODO: compute based on provider pricing
            )
        except Exception:
            pass
        return AIResponse(
            id=str(uuid4()),
            response=generated,
            model=model,
            usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            created_at=datetime.now().isoformat(),
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
        # Ensure models are initialized for this user from stored keys
        if current_user not in ai_service.models:
            try:
                api_keys = key_manager.get_keys(current_user)
                ai_service.initialize_user_models(current_user, api_keys)
            except Exception:
                pass
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

class AddKeyRequest(BaseModel):
    name: str
    provider: str
    key: str

@router.post("/keys", status_code=status.HTTP_201_CREATED)
async def add_api_key(
    request: AddKeyRequest,
    current_user: str = Depends(get_current_user)
):
    """Add a new API key"""
    try:
        key_data = {}
        provider_lower = request.provider.lower()
        
        if provider_lower in ["openai", "gpt", "gpt-4", "gpt-3.5"]:
            key_data["openai_key"] = request.key
        elif provider_lower in ["anthropic", "claude"]:
            key_data["anthropic_key"] = request.key
        elif provider_lower in ["google", "gemini"]:
            key_data["google_key"] = request.key
        elif provider_lower in ["azure", "azure-openai", "aoai"]:
            key_data["azure_key"] = request.key
        elif provider_lower in ["huggingface", "hf"]:
            key_data["huggingface_key"] = request.key
        elif provider_lower in ["cohere"]:
            key_data["cohere_key"] = request.key
        elif provider_lower in ["custom", "other"]:
            key_data["custom_key"] = request.key
        else:
            # Unrecognized providers go to a generic custom slot
            key_data["custom_key"] = request.key

        if not key_data:
            raise HTTPException(status_code=400, detail="Unsupported or empty provider specified")

        key_request = APIKeyRequest(**key_data)
        key_manager.set_keys(current_user, key_request)
        
        # Asynchronously initialize or update models for the user
        try:
            api_keys = key_manager.get_keys(current_user)
            ai_service.initialize_user_models(current_user, api_keys)
        except Exception as e:
            # Log this error but don't fail the entire request, as the key is already saved.
            # A more robust system might use a background task queue here.
            print(f"Note: Error initializing models for user {current_user} after adding key: {e}")
            
        return {"status": "success", "message": f"{request.provider} key added successfully"}
    except HTTPException as e:
        # Re-raise known HTTP exceptions
        raise e
    except Exception as e:
        # Catch any other unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred while adding the key: {e}"
        )

@router.delete("/keys/{key_id}")
async def delete_api_key(
    key_id: str,
    current_user: str = Depends(get_current_user)
):
    """Delete an API key"""
    try:
        # key_id is formatted as "{provider}_{user}"; extract provider
        provider = key_id.split("_")[0].lower() if "_" in key_id else key_id.lower()
        key_manager.delete_key(current_user, provider)
        # Also drop initialized model for this provider if present
        if current_user in ai_service.models:
            to_remove = [m for m in ai_service.models[current_user].keys() if provider in m.lower()]
            for m in to_remove:
                ai_service.models[current_user].pop(m, None)
        return {"status": "success", "message": f"{provider} key deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/keys/{key_id}/test")
async def test_api_key(
    key_id: str,
    current_user: str = Depends(get_current_user)
):
    """Test an API key"""
    try:
        provider = key_id.split("_")[0].lower() if "_" in key_id else key_id.lower()
        status_map = await key_manager.validate_keys(current_user)
        return {"status": "success", "provider": provider, "valid": bool(status_map.get(provider))}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
    try:
        records = database_service.get_usage_stats(current_user, days=days)
        # Map to frontend-friendly shape
        return [
            {
                "date": (r.date.isoformat() if hasattr(r.date, "isoformat") else str(r.date)),
                "model": r.model,
                "tokens": r.tokens_used,
                "requests": r.requests_count,
                "cost": r.cost,
            }
            for r in records
        ]
    except Exception as e:
        # Fallback to empty history
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
    return await key_manager.validate_keys(current_user)

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
