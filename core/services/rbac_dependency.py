"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

from typing import Callable
from fastapi import Depends, HTTPException, status

from core.services.auth import get_current_user
from core.services.rbac import rbac_service


def require_permission(permission: str) -> Callable:
    async def _checker(current_user: str = Depends(get_current_user)):
        perms = rbac_service.get_user_permissions(current_user)
        if permission not in perms:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
        return True

    return _checker
