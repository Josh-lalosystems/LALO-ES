from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List

from ..services.auth import get_current_user
from ..tools.registry import tool_registry
from ..services.audit_logger import audit_logger
try:
    import core.tools  # ensure tools are registered on import
except Exception:
    # Tools package may be partially present; continue with empty registry
    core = None  # type: ignore

router = APIRouter(prefix="/api/admin/tools")


class ToolToggleRequest(BaseModel):
    enabled: bool


@router.get("")
async def list_tools(current_user: str = Depends(get_current_user)):
    """List all tools with status and permissions. Admin-only in production; allowed in DEMO mode."""
    try:
        return tool_registry.list_tools_info()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{tool_name}/enable")
async def enable_tool(tool_name: str, current_user: str = Depends(get_current_user)):
    """Enable a tool by name"""
    ok = tool_registry.enable_tool(tool_name)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Tool '{tool_name}' not found")
    audit_logger.record(action="tool.enable", user_id=current_user, resource=tool_name)
    return {"status": "enabled", "tool": tool_name}


@router.post("/{tool_name}/disable")
async def disable_tool(tool_name: str, current_user: str = Depends(get_current_user)):
    """Disable a tool by name"""
    ok = tool_registry.disable_tool(tool_name)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Tool '{tool_name}' not found")
    audit_logger.record(action="tool.disable", user_id=current_user, resource=tool_name)
    return {"status": "disabled", "tool": tool_name}


@router.put("/{tool_name}")
async def toggle_tool(tool_name: str, payload: ToolToggleRequest, current_user: str = Depends(get_current_user)):
    """Enable/disable a tool by name with a boolean payload"""
    ok = tool_registry.enable_tool(tool_name) if payload.enabled else tool_registry.disable_tool(tool_name)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Tool '{tool_name}' not found")
    audit_logger.record(action=("tool.enable" if payload.enabled else "tool.disable"), user_id=current_user, resource=tool_name)
    return {"status": "enabled" if payload.enabled else "disabled", "tool": tool_name}
