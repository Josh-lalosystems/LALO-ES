from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, List
from pydantic import BaseModel

from services.key_management import key_manager, APIKeyRequest
from services.ai_service import ai_service
from services.auth import get_current_user

router = APIRouter(prefix="/api")

class ModelResponse(BaseModel):
    name: str
    type: str
    status: bool

@router.post("/keys")
async def set_api_keys(
    keys: APIKeyRequest,
    current_user: str = Depends(get_current_user)
):
    """Set API keys for the current user"""
    try:
        key_manager.set_keys(current_user, keys)
        # Initialize models for the user
        api_keys = key_manager.get_keys(current_user)
        ai_service.initialize_user_models(current_user, api_keys)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

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
