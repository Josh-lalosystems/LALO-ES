"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

from fastapi import FastAPI, WebSocket, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import logging
from datetime import datetime
import uuid
from typing import List, Optional

from models import (
    BrowserAction,
    AutomationScript,
    NavigationResult,
    InteractionResult,
    AutomationResult,
    TabInfo
)
from services.browser_manager import BrowserManager
from services.automation_engine import AutomationEngine
from services.auth import get_current_user

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="LALO Browser Control Service")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
browser_manager = BrowserManager()
automation_engine = AutomationEngine(browser_manager)

@app.websocket("/ws/browser/{tab_id}")
async def websocket_endpoint(websocket: WebSocket, tab_id: str):
    await websocket.accept()
    try:
        await browser_manager.connect_websocket(tab_id, websocket)
        while True:
            data = await websocket.receive_json()
            await browser_manager.handle_message(tab_id, data)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
    finally:
        await browser_manager.disconnect_websocket(tab_id)

@app.post("/browser/navigate", response_model=NavigationResult)
async def navigate(
    url: str,
    tab_id: Optional[str] = None,
    current_user: str = Depends(get_current_user)
) -> NavigationResult:
    try:
        return await browser_manager.navigate(url, tab_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/browser/interact", response_model=InteractionResult)
async def interact(
    action: BrowserAction,
    tab_id: str,
    current_user: str = Depends(get_current_user)
) -> InteractionResult:
    try:
        return await browser_manager.interact(action, tab_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/automation/script", response_model=AutomationScript)
async def create_script(
    name: str,
    description: str,
    actions: List[BrowserAction],
    current_user: str = Depends(get_current_user)
) -> AutomationScript:
    try:
        script = AutomationScript(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            actions=actions,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            created_by=current_user
        )
        return await automation_engine.save_script(script)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/automation/run/{script_id}", response_model=AutomationResult)
async def run_script(
    script_id: str,
    current_user: str = Depends(get_current_user)
) -> AutomationResult:
    try:
        script = await automation_engine.get_script(script_id)
        if not script:
            raise HTTPException(status_code=404, detail="Script not found")
        return await automation_engine.run_script(script)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/browser/tabs", response_model=List[TabInfo])
async def list_tabs(
    current_user: str = Depends(get_current_user)
) -> List[TabInfo]:
    try:
        return await browser_manager.list_tabs()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
