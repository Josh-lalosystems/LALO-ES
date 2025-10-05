"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Optional

from ..services.auth import get_current_user
from ..services.audit_logger import audit_logger

router = APIRouter(prefix="/api/admin/audit")


@router.get("")
async def list_audit_logs(limit: int = 100, offset: int = 0, user_id: Optional[str] = None, action: Optional[str] = None, level: Optional[str] = None, current_user: str = Depends(get_current_user)):
    try:
        return audit_logger.list(limit=limit, offset=offset, user_id=user_id, action=action, level=level)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
