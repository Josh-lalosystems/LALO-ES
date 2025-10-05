"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

from pydantic import BaseSettings


class MCPSettings(BaseSettings):
    FRONTEND_URL: str = "http://localhost:3000"
    FRONTEND_WAIT_SELECTOR: str = "body"
    FRONTEND_TIMEOUT: int = 8

    class Config:
        env_file = ".env"


settings = MCPSettings()
