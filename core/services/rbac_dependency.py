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
