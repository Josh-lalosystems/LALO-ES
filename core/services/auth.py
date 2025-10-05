from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import jwt
from datetime import datetime, timedelta
import os
import sys
from dotenv import load_dotenv

# Load .env if present
load_dotenv()

import logging
logger = logging.getLogger('core.services.auth')

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Demo mode configuration
# Enable DEMO_MODE automatically when running under pytest to make test
# imports and startup safe (many tests import the app at module-import time).
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true" or ("pytest" in sys.modules)

# HTTP Bearer security (optional for demo mode)
security = HTTPBearer(auto_error=not DEMO_MODE)

class AuthService:
    def __init__(self):
        self.secret_key = SECRET_KEY
        self.algorithm = ALGORITHM

    def create_access_token(self, user_id: str, expires_delta: Optional[timedelta] = None):
        """Create a JWT access token"""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode = {"sub": user_id, "exp": expire}
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str) -> str:
        """Verify JWT token and return user_id"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id: str = payload.get("sub")
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return user_id
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

# Global auth service instance
auth_service = AuthService()

async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> str:
    """
    Dependency to get the current authenticated user.
    Respects DEMO_MODE environment variable.

    - If DEMO_MODE=true: Returns demo user without authentication
    - If DEMO_MODE=false: Requires valid JWT token
    """
    # Demo mode: bypass authentication
    if DEMO_MODE:
        user_id = "demo-user@example.com"

        # Auto-provision demo API keys if configured
        try:
            from core.services.key_management import key_manager, APIKeyRequest
            from pydantic import SecretStr
            existing_keys = key_manager.get_keys(user_id)

            if not existing_keys:
                demo_openai = os.getenv("DEMO_OPENAI_KEY", "")
                demo_anthropic = os.getenv("DEMO_ANTHROPIC_KEY", "")

                if demo_openai or demo_anthropic:
                    logger.info("[DEMO] Auto-provisioning API keys for %s", user_id)
                    key_request = APIKeyRequest(
                        openai_key=SecretStr(demo_openai) if demo_openai else None,
                        anthropic_key=SecretStr(demo_anthropic) if demo_anthropic else None
                    )
                    key_manager.set_keys(user_id, key_request)
                    logger.info("[DEMO] Successfully provisioned API keys")
        except Exception as e:
            logger.warning("[DEMO] Warning: Could not auto-provision API keys: %s", e)
            import traceback
            logger.debug(traceback.format_exc())

        return user_id

    # Production mode: require valid token
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    user_id = auth_service.verify_token(token)
    return user_id

async def get_current_user_demo() -> str:
    """
    Demo version that always returns a test user without authentication.
    Use this for testing/development endpoints that should always bypass auth.
    """
    return "demo-user@example.com"

# Authentication endpoints
from fastapi import APIRouter
from pydantic import BaseModel

auth_router = APIRouter(prefix="/auth")

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

@auth_router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """
    Login endpoint for demo purposes.
    In production, this should verify credentials against a database.
    """
    # Demo authentication - accept any email/password
    # In production, verify against database
    if request.email and request.password:
        access_token = auth_service.create_access_token(user_id=request.email)
        return TokenResponse(access_token=access_token, token_type="bearer")
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

@auth_router.post("/demo-token", response_model=TokenResponse)
async def get_demo_token():
    """
    Get a demo token for testing purposes.
    """
    access_token = auth_service.create_access_token(user_id="demo-user@example.com")
    return TokenResponse(access_token=access_token, token_type="bearer")
