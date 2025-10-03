from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

class BrowserAction(BaseModel):
    type: str
    selector: str
    value: Optional[str] = None
    timeout: Optional[int] = 30
    wait_for: Optional[str] = None

class AutomationScript(BaseModel):
    id: str
    name: str
    description: str
    actions: List[BrowserAction]
    created_at: datetime
    updated_at: datetime
    created_by: str
    last_run: Optional[datetime] = None
    success_rate: float = 0.0

class NavigationResult(BaseModel):
    success: bool
    url: str
    status: str
    errors: Optional[List[str]] = None

class InteractionResult(BaseModel):
    success: bool
    action: str
    selector: str
    result: Optional[dict] = None
    errors: Optional[List[str]] = None

class AutomationResult(BaseModel):
    success: bool
    script_id: str
    results: List[InteractionResult]
    start_time: datetime
    end_time: datetime
    errors: Optional[List[str]] = None

class TabInfo(BaseModel):
    id: str
    url: str
    title: str
    status: str
    created_at: datetime
    last_active: datetime
