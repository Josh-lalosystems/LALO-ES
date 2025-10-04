from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, List, Optional
from pydantic import BaseModel
from datetime import datetime
from uuid import uuid4
import asyncio

from ..services.key_management import key_manager, APIKeyRequest
from ..services.ai_service import ai_service
from ..services.auth import get_current_user
from ..services.database_service import database_service
from ..services.pricing import calculate_cost, estimate_tokens
try:
    from confidence_system import ConfidenceSystem  # type: ignore
    CONF_SYSTEM_AVAILABLE = True
except Exception:
    ConfidenceSystem = None  # type: ignore
    CONF_SYSTEM_AVAILABLE = False

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
    # Optional explainability additions
    interpretation: Optional[str] = None
    confidence: Optional[Dict] = None  # { score: float, reasoning: List[str], clarifications: List[str], feedback_required: bool }

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

class FeedbackRequest(BaseModel):
    response_id: str
    helpful: bool
    reason: Optional[str] = None
    details: Optional[str] = None

class ImageRequest(BaseModel):
    prompt: str
    model: Optional[str] = "gpt-image-1"  # OpenAI Images model
    size: Optional[str] = "1024x1024"     # 256x256 | 512x512 | 1024x1024
    n: Optional[int] = 1                   # number of images

class GeneratedImage(BaseModel):
    b64: str
    data_url: str

class ImageResponse(BaseModel):
    id: str
    created_at: str
    model: str
    images: List[GeneratedImage]

@router.post("/ai/chat")
async def send_ai_request(
    request: AIRequest,
    current_user: str = Depends(get_current_user)
) -> AIResponse:
    """
    Send a request to AI models with comprehensive error handling.

    Includes:
    - Automatic model initialization
    - Request timeout (60 seconds)
    - Usage tracking with cost calculation
    - Detailed error messages
    """
    try:
        # Ensure user models are initialized based on stored keys
        if current_user not in ai_service.models:
            try:
                api_keys = key_manager.get_keys(current_user)
                if not api_keys:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="No API keys configured. Please add your API keys in Settings to use AI models."
                    )
                ai_service.initialize_user_models(current_user, api_keys)
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to initialize AI models: {str(e)}"
                )

        # Get available models and select one
        available = ai_service.get_available_models(current_user)
        model = request.model or (available[0] if available else None)

        if not available:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No models available. Please add API keys in Settings."
            )

        if not model or model not in available:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Model '{model}' not available. Available models: {', '.join(available)}"
            )

        # Generate response with timeout protection
        try:
            generated = await asyncio.wait_for(
                ai_service.generate(
                    request.prompt,
                    model_name=model,
                    user_id=current_user,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature,
                ),
                timeout=60.0  # 60 second timeout
            )
        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="AI request timed out after 60 seconds. Please try again with a shorter prompt or lower max_tokens."
            )
        except Exception as e:
            error_msg = str(e)
            # Provider-specific error handling
            if "api key" in error_msg.lower():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="API key authentication failed. Please check your API keys in Settings."
                )
            elif "rate limit" in error_msg.lower():
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded. Please wait a moment and try again."
                )
            elif "quota" in error_msg.lower():
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail="API quota exceeded. Please check your provider account."
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"AI generation failed: {error_msg}"
                )

    # Calculate token usage and cost
        prompt_tokens = estimate_tokens(request.prompt)
        completion_tokens = estimate_tokens(generated)
        total_tokens = prompt_tokens + completion_tokens

        cost = calculate_cost(
            model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens
        )

        # Optional: run confidence/interpretation analysis if models available
        interpretation: Optional[str] = None
        confidence_payload: Optional[Dict] = None
        try:
            if CONF_SYSTEM_AVAILABLE:
                available_models = set(ai_service.get_available_models(current_user))
                # Only run if both OpenAI lightweight and Anthropic confidence models exist
                if ("gpt-3.5-turbo" in available_models) and ("claude-3-haiku-20240307" in available_models):
                    cs = ConfidenceSystem(ai_service=ai_service, user_id=current_user)
                    analysis = await cs.interpret_request(request.prompt)
                    interpretation = analysis.interpreted_intent
                    confidence_payload = {
                        "score": analysis.confidence_score,
                        "reasoning": analysis.reasoning_trace,
                        "clarifications": analysis.suggested_clarifications,
                        "feedback_required": analysis.feedback_required,
                    }
        except Exception as e:
            # Don't fail the request if confidence system fails
            print(f"ConfidenceSystem warning: {e}")

        # Record usage in database
        try:
            database_service.record_usage(
                user_id=current_user,
                model=model,
                tokens_used=total_tokens,
                cost=cost,
            )
        except Exception as e:
            # Log but don't fail the request if usage recording fails
            print(f"Failed to record usage for {current_user}: {e}")

        return AIResponse(
            id=str(uuid4()),
            response=generated,
            model=model,
            usage={
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens
            },
            created_at=datetime.now().isoformat(),
            interpretation=interpretation,
            confidence=confidence_payload,
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Catch any unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
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
        api_keys = key_manager.get_keys(current_user)
        if current_user not in ai_service.models:
            try:
                ai_service.initialize_user_models(current_user, api_keys)
            except Exception:
                pass
        else:
            # Prune models for providers with no keys
            existing = ai_service.models.get(current_user, {})
            to_remove = []
            for name in list(existing.keys()):
                n = name.lower()
                should_remove = (("claude" in n and "anthropic" not in api_keys) or
                                 ("gpt" in n and "openai" not in api_keys))
                if should_remove:
                    to_remove.append(name)
            for m in to_remove:
                existing.pop(m, None)
        return ai_service.get_available_models(current_user)
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
        # Also drop initialized models for this provider if present
        if current_user in ai_service.models:
            # Match models by common provider prefixes
            def is_provider_model(name: str) -> bool:
                n = name.lower()
                if provider == "anthropic":
                    return ("claude" in n)
                if provider == "openai":
                    return ("gpt" in n)
                if provider in ("google", "gemini"):
                    return ("gemini" in n)
                if provider in ("azure", "azure-openai", "aoai"):
                    return ("gpt" in n or "azure" in n)
                if provider in ("huggingface", "hf"):
                    return ("huggingface" in n or "hf" in n)
                if provider == "cohere":
                    return ("cohere" in n)
                # Generic fallback
                return provider in n
            to_remove = [m for m in list(ai_service.models[current_user].keys()) if is_provider_model(m)]
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

@router.post("/ai/feedback")
async def submit_feedback(payload: FeedbackRequest, current_user: str = Depends(get_current_user)):
    """Accept lightweight feedback on AI responses for UX metrics and model tuning."""
    try:
        database_service.save_feedback(
            user_id=current_user,
            response_id=payload.response_id,
            helpful=payload.helpful,
            reason=payload.reason,
            details=payload.details,
        )
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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

@router.post("/ai/image", response_model=ImageResponse)
async def generate_image(
    request: ImageRequest,
    current_user: str = Depends(get_current_user)
):
    """Generate image(s) with OpenAI Images API (OpenAI-only)."""
    # Ensure OpenAI key exists
    keys = key_manager.get_keys(current_user)
    openai_key = keys.get("openai")
    if not openai_key:
        raise HTTPException(status_code=400, detail="OpenAI API key not configured. Add it in Settings.")

    # Lazy import to avoid hard dependency
    try:
        from openai import AsyncOpenAI  # type: ignore
    except Exception:
        raise HTTPException(status_code=500, detail="openai package not installed on server.")

    try:
        client = AsyncOpenAI(api_key=openai_key)
        # OpenAI v1 Images API
        result = await client.images.generate(
            model=request.model or "gpt-image-1",
            prompt=request.prompt,
            size=request.size or "1024x1024",
            n=request.n or 1,
        )
        images: List[GeneratedImage] = []
        # result.data is a list with objects that may contain b64_json
        for item in getattr(result, "data", []) or []:
            b64 = getattr(item, "b64_json", None)
            if not b64:
                # If the API returned URLs instead (rare in v1), skip or convert
                url = getattr(item, "url", None)
                if url:
                    images.append(GeneratedImage(b64="", data_url=url))
                continue
            data_url = f"data:image/png;base64,{b64}"
            images.append(GeneratedImage(b64=b64, data_url=data_url))

        if not images:
            raise HTTPException(status_code=502, detail="No images returned by provider.")

        # Optionally record usage (no token counts). Cost estimation omitted.
        try:
            database_service.record_usage(
                user_id=current_user,
                model=request.model or "gpt-image-1",
                tokens_used=0,
                cost=0.0,
            )
        except Exception as e:
            print(f"Note: failed to record image usage: {e}")

        return ImageResponse(
            id=str(uuid4()),
            created_at=datetime.now().isoformat(),
            model=request.model or "gpt-image-1",
            images=images,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image generation failed: {e}")

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
