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
Pydantic Validation Schemas
"""

from pydantic import BaseModel, Field, validator, EmailStr
from typing import List, Optional, Dict, Any
from enum import Enum


class ModelName(str, Enum):
    GPT4_TURBO = "gpt-4-turbo-preview"
    GPT35_TURBO = "gpt-3.5-turbo"
    CLAUDE_SONNET = "claude-3-5-sonnet-20241022"
    CLAUDE_OPUS = "claude-3-opus-20240229"
    CLAUDE_HAIKU = "claude-3-haiku-20240307"


class WorkflowRequestSchema(BaseModel):
    user_request: str = Field(..., min_length=1, max_length=10000)
    prebuilt_workflow_id: Optional[str] = Field(None, pattern=r'^[a-zA-Z0-9\-]+$')

    @validator('user_request')
    def sanitize_request(cls, v):
        from .input_validators import sanitize_xss
        return sanitize_xss(v)


class ToolInputSchema(BaseModel):
    tool_name: str = Field(..., min_length=1, max_length=100)
    parameters: Dict[str, Any] = Field(default_factory=dict)

    @validator('tool_name')
    def validate_tool_name(cls, v):
        # Only alphanumeric and underscores
        import re
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError("Tool name can only contain alphanumeric and underscores")
        return v


class AgentConfigSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, pattern=r'^[a-zA-Z0-9\-_ ]+$')
    description: Optional[str] = Field(None, max_length=500)
    system_prompt: str = Field(..., min_length=1, max_length=5000)
    model: ModelName = Field(default=ModelName.GPT35_TURBO)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2000, ge=1, le=100000)
    allowed_tools: List[str] = Field(default_factory=list)
    guardrails: List[str] = Field(default_factory=list)
    is_public: bool = Field(default=False)

    @validator('name', 'system_prompt')
    def sanitize_text(cls, v):
        from .input_validators import sanitize_xss
        return sanitize_xss(v)

    @validator('allowed_tools')
    def validate_tools(cls, v):
        from .input_validators import sanitize_xss
        return [sanitize_xss(tool) for tool in v]


class APIKeySchema(BaseModel):
    provider: str = Field(..., pattern=r'^(openai|anthropic)$')
    api_key: str = Field(..., min_length=10)

    @validator('api_key')
    def validate_key_format(cls, v, values):
        from .input_validators import validate_api_key
        provider = values.get('provider')
        if provider and not validate_api_key(v, provider):
            raise ValueError(f"Invalid {provider} API key format")
        return v


class UserRegistrationSchema(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    name: Optional[str] = Field(None, max_length=100)

    @validator('password')
    def validate_password(cls, v):
        # Password must have: uppercase, lowercase, number
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")
        return v

    @validator('name')
    def sanitize_name(cls, v):
        if v:
            from .input_validators import sanitize_xss
            return sanitize_xss(v)
        return v


class SessionConfigSchema(BaseModel):
    timeout_minutes: int = Field(default=30, ge=5, le=1440)  # 5 min to 24 hours
    remember_me: bool = Field(default=False)
    max_concurrent_sessions: int = Field(default=3, ge=1, le=10)


class RateLimitSchema(BaseModel):
    requests_per_minute: int = Field(default=60, ge=1, le=1000)
    requests_per_hour: int = Field(default=1000, ge=1, le=100000)
    requests_per_day: int = Field(default=10000, ge=1, le=1000000)
