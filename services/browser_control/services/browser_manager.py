"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

import logging
from typing import Dict, List, Optional
from fastapi import WebSocket
from datetime import datetime

from models import (
    BrowserAction,
    NavigationResult,
    InteractionResult,
    TabInfo
)
from .chrome_client import ChromeClient

logger = logging.getLogger(__name__)

class BrowserManager:
    def __init__(self):
        self.tabs: Dict[str, ChromeClient] = {}
        self.websockets: Dict[str, WebSocket] = {}
        
    async def connect_websocket(self, tab_id: str, websocket: WebSocket):
        """Connect a WebSocket to a specific tab."""
        self.websockets[tab_id] = websocket
        if tab_id not in self.tabs:
            self.tabs[tab_id] = ChromeClient()
            await self.tabs[tab_id].connect()
            
    async def disconnect_websocket(self, tab_id: str):
        """Disconnect a WebSocket from a specific tab."""
        if tab_id in self.websockets:
            del self.websockets[tab_id]
        if tab_id in self.tabs:
            await self.tabs[tab_id].disconnect()
            del self.tabs[tab_id]
            
    async def handle_message(self, tab_id: str, message: dict):
        """Handle incoming WebSocket messages."""
        if tab_id not in self.tabs:
            logger.error(f"Tab {tab_id} not found")
            return
            
        action_type = message.get("type")
        if action_type == "navigation":
            result = await self.navigate(message["url"], tab_id)
        elif action_type == "interaction":
            action = BrowserAction(**message["action"])
            result = await self.interact(action, tab_id)
        else:
            logger.warning(f"Unknown message type: {action_type}")
            return
            
        # Send result back through WebSocket
        if tab_id in self.websockets:
            await self.websockets[tab_id].send_json(result.dict())
            
    async def navigate(self, url: str, tab_id: Optional[str] = None) -> NavigationResult:
        """Navigate to a URL in a specific tab or create a new tab."""
        if not tab_id:
            tab_id = str(len(self.tabs))
            self.tabs[tab_id] = ChromeClient()
            await self.tabs[tab_id].connect()
            
        if tab_id not in self.tabs:
            raise ValueError(f"Tab {tab_id} not found")
            
        start_time = datetime.utcnow()
        success = await self.tabs[tab_id].navigate(url)
        end_time = datetime.utcnow()
        
        return NavigationResult(
            success=success,
            url=url,
            tab_id=tab_id,
            start_time=start_time,
            end_time=end_time
        )
        
    async def interact(self, action: BrowserAction, tab_id: str) -> InteractionResult:
        """Execute a browser action in a specific tab."""
        if tab_id not in self.tabs:
            raise ValueError(f"Tab {tab_id} not found")
            
        start_time = datetime.utcnow()
        result = await self.tabs[tab_id].execute_action(action)
        end_time = datetime.utcnow()
        
        return InteractionResult(
            success=result["success"],
            action=action,
            tab_id=tab_id,
            start_time=start_time,
            end_time=end_time,
            error=result.get("error"),
            data=result.get("data")
        )
        
    async def list_tabs(self) -> List[TabInfo]:
        """List all active browser tabs."""
        tabs = []
        for tab_id, client in self.tabs.items():
            info = await client.get_tab_info()
            tabs.append(TabInfo(
                id=tab_id,
                url=info["url"],
                title=info["title"],
                status=info["status"]
            ))
        return tabs
