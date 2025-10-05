"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from typing import Callable

from ..services.auth import get_current_user, DEMO_MODE
from ..services.rbac import rbac_service


class RBACMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Best-effort attach permissions; avoid failing requests here.
        try:
            user_id = None
            if DEMO_MODE:
                user_id = "demo-user@example.com"
            else:
                # In non-demo we rely on route dependencies for auth
                # Here we can parse Authorization header if needed.
                auth = request.headers.get("authorization")
                if auth and auth.lower().startswith("bearer "):
                    # We cannot call dependency directly; leave None
                    user_id = None
            if user_id:
                perms = rbac_service.get_user_permissions(user_id)
                request.state.permissions = perms
        except Exception:
            request.state.permissions = set()
        return await call_next(request)
