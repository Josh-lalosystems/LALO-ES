from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Set

from ..services.auth import get_current_user
from ..services.rbac import rbac_service
from ..services.audit_logger import audit_logger

router = APIRouter(prefix="/api/admin/rbac")


class AssignRoleRequest(BaseModel):
    user_id: str
    role: str


@router.post("/assign")
async def assign_role(payload: AssignRoleRequest, current_user: str = Depends(get_current_user)):
    try:
        # In a production system, verify current_user has admin rights
        rbac_service.assign_role_to_user(payload.user_id, payload.role)
        audit_logger.record(action="rbac.assign_role", user_id=current_user, resource=payload.user_id, details={"role": payload.role})
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}/permissions")
async def get_user_permissions(user_id: str, current_user: str = Depends(get_current_user)) -> List[str]:
    try:
        perms = rbac_service.get_user_permissions(user_id)
        return sorted(list(perms))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/roles/{role}/permissions/{perm}")
async def grant_permission(role: str, perm: str, current_user: str = Depends(get_current_user)):
    try:
        rbac_service.grant_permission_to_role(role, perm)
        audit_logger.record(action="rbac.grant_permission", user_id=current_user, resource=role, details={"permission": perm})
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
