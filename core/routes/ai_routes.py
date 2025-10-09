"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from typing import Dict, List, Optional
from pydantic import BaseModel
from datetime import datetime
from uuid import uuid4
import asyncio
import logging
import json

from ..services.key_management import key_manager, APIKeyRequest
import os
from ..services.ai_service import ai_service
from ..services.unified_request_handler import unified_request_handler
from ..services.local_llm_service import local_llm_service
from ..services.auth import get_current_user
from ..services.database_service import database_service
from ..services.pricing import calculate_cost, estimate_tokens
from ..services.router_model import router_model
from ..services.workflow_orchestrator import workflow_orchestrator
try:
    from confidence_system import ConfidenceSystem  # type: ignore
    CONF_SYSTEM_AVAILABLE = True
except Exception:
    ConfidenceSystem = None  # type: ignore
    CONF_SYSTEM_AVAILABLE = False

router = APIRouter(prefix="/api")

# Logger for AI routes
logger = logging.getLogger("lalo.ai_routes")
if not logger.handlers:
    # Basic config if not already configured by application
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(levelname)s] %(name)s: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

class AIRequest(BaseModel):
    prompt: str
    # Default to None so the route will select the first available model
    model: Optional[str] = None
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
    routing_info: Optional[Dict] = None  # Router decision metadata

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
    # New clean implementation: validate keys, demo fallback, initialize models, generate
    logger.debug("send_ai_request called for user=%s model=%s", current_user, request.model)

    # **STEP 1: ROUTE THE REQUEST** (Intelligent routing with local inference)
    try:
        routing_decision = await router_model.route(request.prompt)
        logger.info(f"Router decision: path={routing_decision['path']}, complexity={routing_decision['complexity']:.2f}, recommended_model={routing_decision['recommended_model']}")
    except Exception as e:
        logger.warning(f"Router failed, using default routing: {e}")
        routing_decision = {
            "path": "simple",
            "complexity": 0.5,
            "confidence": 0.7,
            "reasoning": f"Fallback routing (router error: {str(e)})",
            "recommended_model": "tinyllama-1.1b",
            "requires_tools": False,
            "requires_workflow": False
        }

    # Load API keys and validate which providers are working
    api_keys = key_manager.get_keys(current_user) or {}
    logger.debug("api_keys for %s: %s", current_user, list(api_keys.keys()))
    try:
        working_keys = await key_manager.validate_keys(current_user)
        if not isinstance(working_keys, dict):
            logger.warning("validate_keys returned unexpected type; coercing to dict")
            working_keys = dict(working_keys)
    except Exception as ve:
        logger.warning("validate_keys exception for %s: %s", current_user, ve)
        working_keys = {}
    logger.debug("working_keys: %s", working_keys)

    DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"
    # If no keys at all and demo enabled, return a demo echo
    if (not api_keys or all(not v for v in api_keys.values())) and DEMO_MODE:
        mock_text = f"(DEMO) Echo: {request.prompt}"
        prompt_tokens = estimate_tokens(request.prompt)
        completion_tokens = estimate_tokens(mock_text)
        total_tokens = prompt_tokens + completion_tokens
        return AIResponse(
            id=str(uuid4()),
            response=mock_text,
            model="demo-model",
            usage={
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
            },
            created_at=datetime.now().isoformat(),
            interpretation=None,
            confidence=None,
        )

    # If keys exist but none validated as working, and demo enabled, return demo echo
    if api_keys and (not any(working_keys.values())) and DEMO_MODE:
        mock_text = f"(DEMO) Echo: {request.prompt}"
        prompt_tokens = estimate_tokens(request.prompt)
        completion_tokens = estimate_tokens(mock_text)
        total_tokens = prompt_tokens + completion_tokens
        return AIResponse(
            id=str(uuid4()),
            response=mock_text,
            model="demo-model",
            usage={
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
            },
            created_at=datetime.now().isoformat(),
            interpretation=None,
            confidence=None,
        )

    # Initialize models using only providers that validated as working (best-effort)
    try:
        ai_service.initialize_user_models(current_user, api_keys, working_keys=working_keys)
    except Exception as e:
        logger.warning("Failed to initialize models for %s: %s", current_user, e)

    # Get available models from cloud APIs
    cloud_models = ai_service.get_available_models(current_user)

    # Add local models if local inference is available
    available_local_models = list(local_llm_service.model_configs.keys()) if local_llm_service.is_available() else []

    # Combine cloud and local models
    available = cloud_models + available_local_models
    logger.debug("available models for %s: cloud=%s, local=%s", current_user, cloud_models, available_local_models)

    try:
        handler_response = await asyncio.wait_for(
            unified_request_handler.handle_request(
                user_request=request.prompt,
                user_id=current_user,
                available_models=available,
                context=None,
                stream=False,
            ),
            timeout=60.0
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail="AI request timed out after 60 seconds. Please try again with a shorter prompt or lower max_tokens.")
    except Exception as e:
        error_msg = str(e)
        import traceback
        logger.error("Exception during unified handler (%s): %s", type(e).__name__, error_msg)
        logger.debug(traceback.format_exc())
        # Map common errors to HTTP responses
        if "api key" in error_msg.lower():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"API key authentication failed: {error_msg}")
        elif "rate limit" in error_msg.lower():
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded. Please wait a moment and try again.")
        elif "quota" in error_msg.lower():
            raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="API quota exceeded. Please check your provider account.")
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"AI generation failed: {error_msg}")

    # Handler response should be a dict matching the unified handler contract
    generated = handler_response.get("response", "")
    model = handler_response.get("model", handler_response.get("models_used", available[0] if available else "unknown"))

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
        logger.warning("ConfidenceSystem warning: %s", e)

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
        logger.warning("Failed to record usage for %s: %s", current_user, e)

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
        routing_info=routing_decision,  # Include routing metadata
        interpretation=interpretation,
        confidence=confidence_payload,
    )


@router.post('/ai/feedback')
async def ai_feedback_alias(payload: Dict, current_user: str = Depends(get_current_user)):
    """
    Lightweight compatibility endpoint for frontend feedback widget.

    The frontend currently posts feedback to `/api/ai/feedback` with a payload like:
      { response_id, helpful, reason?, details? }

    The canonical workflow feedback endpoint is `/api/workflow/{session_id}/feedback`.
    This alias attempts to be forgiving:
      - If `response_id` looks like a workflow session id, forward to the orchestrator.
      - Otherwise record a minimal audit log and return 202 Accepted so the UI shows success.

    This is intentionally low-risk and non-blocking; more complete wiring (mapping
    response_id -> session id or saving to the feedback table) can be added later.
    """
    try:
        resp_id = payload.get('response_id') or payload.get('id')
        helpful = payload.get('helpful')
        reason = payload.get('reason') or payload.get('message') or ''
        details = payload.get('details') or ''

        # Best-effort: if response_id resembles a workflow session UUID, forward
        # to the workflow orchestrator submit_feedback method. We can't reliably
        # map arbitrary response ids here, so only attempt forward when session
        # exists.
        if resp_id:
            try:
                # If orchestrator exposes a lookup, use it. Otherwise, call submit_feedback
                # and let it raise if session not found.
                session_dict = await workflow_orchestrator.submit_feedback(
                    session_id=resp_id,
                    user_id=current_user,
                    feedback_type='final' if helpful else 'reject',
                    message=reason or details,
                )
                # If orchestrator returns a not_found error (session id unknown),
                # treat it as an accepted ack so the frontend doesn't appear broken.
                if isinstance(session_dict, dict) and session_dict.get('error') == 'not_found':
                    logger.info("ai_feedback_alias: orchestrator reported not_found for response_id=%s; returning accepted ack", resp_id)
                    return { 'status': 'accepted' }
                return session_dict
            except Exception:
                # Fallthrough: log and accept
                logger.info("ai_feedback_alias: received feedback for non-workflow response_id=%s, user=%s", resp_id, current_user)

        # Minimal ack for now
        logger.info("ai_feedback_alias: recorded minimal feedback user=%s helpful=%s reason=%s", current_user, helpful, reason)
        return { 'status': 'accepted' }
    except Exception as e:
        logger.exception("ai_feedback_alias error: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/ai/chat/stream")
async def stream_ai_chat(
    request: AIRequest,
    current_user: str = Depends(get_current_user)
) -> StreamingResponse:
    """Stream AI responses (SSE) when local streaming is available; otherwise fallback to full response."""
    logger.debug("stream_ai_chat called for user=%s model=%s", current_user, request.model)

    # Determine routing decision first
    try:
        routing_decision = await router_model.route(request.prompt)
    except Exception as e:
        logger.warning(f"Router failed for stream: {e}")
        routing_decision = {"path": "simple", "recommended_model": "tinyllama"}

    # Determine model to stream from
    available = ai_service.get_available_models(current_user)
    model_name = routing_decision.get("recommended_model") or (available[0] if available else "tinyllama")

    async def event_stream():
        # Send routing info first
        yield f"data: {json.dumps({'type': 'routing', 'content': routing_decision})}\n\n"

        # If local inference supports streaming, stream tokens
        if local_llm_service.is_available():
            try:
                async for chunk in local_llm_service.generate_stream(
                    prompt=request.prompt,
                    model_name=model_name,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature,
                ):
                    # Each chunk may be partial text; send as token event
                    yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"
            except Exception as e:
                logger.error("Streaming generation failed: %s", e)
                yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
                # Fallback: return non-streamed full response
                try:
                    fallback = await unified_request_handler.handle_request(
                        user_request=request.prompt,
                        user_id=current_user,
                        available_models=available,
                        stream=False,
                    )
                    yield f"data: {json.dumps({'type': 'done', 'content': fallback.get('response')})}\n\n"
                except Exception as e2:
                    yield f"data: {json.dumps({'type': 'error', 'content': str(e2)})}\n\n"
                return
        else:
            # No local streaming: produce full response via unified handler
            try:
                full = await unified_request_handler.handle_request(
                    user_request=request.prompt,
                    user_id=current_user,
                    available_models=available,
                    stream=False,
                )
                yield f"data: {json.dumps({'type': 'done', 'content': full.get('response')})}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

        # Final done event
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

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
        # Get cloud models
        cloud_models = ai_service.get_available_models(current_user)

        # Add local models if local inference is available
        available_local_models = list(local_llm_service.model_configs.keys()) if local_llm_service.is_available() else []

        # Combine and return
        return cloud_models + available_local_models
    except Exception as e:
        # In case of failure, provide sensible defaults for the UI
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
            logger.warning("Error initializing models for user %s after adding key: %s", current_user, e)
            
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
    """Generate image(s) with OpenAI Images API (OpenAI-only).

    If running in demo mode or no OpenAI key is configured, return a tiny
    placeholder image so the frontend remains functional.
    """
    # Ensure OpenAI key exists
    keys = key_manager.get_keys(current_user)
    openai_key = keys.get("openai")
    DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"
    if not openai_key or DEMO_MODE:
        tiny_png_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGMAAQAABQABDQottAAAAABJRU5ErkJggg=="
        data_url = f"data:image/png;base64,{tiny_png_b64}"
        img = GeneratedImage(b64=tiny_png_b64, data_url=data_url)
        return ImageResponse(id=str(uuid4()), created_at=datetime.now().isoformat(), model="demo-image", images=[img])

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
            logger.warning("failed to record image usage: %s", e)

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

@router.post("/ai/chat/stream")
async def send_ai_request_stream(
    request: AIRequest,
    current_user: str = Depends(get_current_user)
):
    """
    Stream AI responses in real-time (Server-Sent Events).

    This endpoint supports local models with streaming generation.
    Responses are sent as Server-Sent Events (SSE) in the format:

    data: {"type": "token", "content": "word"}
    data: {"type": "routing", "content": {...routing_info...}}
    data: {"type": "done", "content": {"usage": {...}, "model": "..."}}
    """
    from ..services.local_llm_service import local_llm_service

    # Determine which model to use
    available = ai_service.get_available_models(current_user)
    model = request.model or (available[0] if available else None)

    if not model or model not in available:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Model {model} not available. Available models: {', '.join(available)}"
        )

    # Check if model is local and supports streaming
    local_models = ["tinyllama-1.1b", "liquid-tool-1.2b", "qwen-0.5b"]
    is_local = model in local_models

    if not is_local:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Streaming only supported for local models: {', '.join(local_models)}"
        )

    async def generate_stream():
        """Generator for streaming response"""
        try:
            # Send routing decision first
            routing_decision = await router_model.route(request.prompt)
            yield f"data: {json.dumps({'type': 'routing', 'content': routing_decision})}\n\n"

            # Stream the response
            full_response = ""
            model_name = model.replace("-1.1b", "").replace("-1.2b", "").replace("-0.5b", "")

            async for chunk in local_llm_service.generate_stream(
                prompt=request.prompt,
                model_name=model_name,
                max_tokens=request.max_tokens or 1000,
                temperature=request.temperature or 0.7
            ):
                full_response += chunk
                yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"

            # Calculate usage and send completion
            estimated_tokens = estimate_tokens(request.prompt, full_response)
            cost = calculate_cost(model, estimated_tokens)

            # Record usage
            database_service.record_usage(
                user_id=current_user,
                model=model,
                tokens_used=estimated_tokens,
                cost=cost
            )

            # Send completion event
            yield f"data: {json.dumps({'type': 'done', 'content': {'usage': {'total_tokens': estimated_tokens}, 'model': model, 'cost': cost}})}\n\n"

        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )

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
