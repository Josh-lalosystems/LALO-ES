"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

import logging
from typing import Dict, Optional
from datetime import datetime

from models import (
    AutomationScript,
    AutomationResult,
    BrowserAction
)
from .browser_manager import BrowserManager

logger = logging.getLogger(__name__)

class AutomationEngine:
    def __init__(self, browser_manager: BrowserManager):
        self.browser_manager = browser_manager
        self.scripts: Dict[str, AutomationScript] = {}
        
    async def save_script(self, script: AutomationScript) -> AutomationScript:
        """Save an automation script."""
        self.scripts[script.id] = script
        return script
        
    async def get_script(self, script_id: str) -> Optional[AutomationScript]:
        """Retrieve an automation script by ID."""
        return self.scripts.get(script_id)
        
    async def run_script(self, script: AutomationScript) -> AutomationResult:
        """Execute an automation script."""
        start_time = datetime.utcnow()
        tab_id = None
        results = []
        success = True
        error = None
        
        try:
            # Execute each action in sequence
            for action in script.actions:
                if action.type == "navigation":
                    result = await self.browser_manager.navigate(
                        action.url,
                        tab_id
                    )
                    tab_id = result.tab_id
                else:
                    if not tab_id:
                        raise ValueError("No active tab for interaction")
                    result = await self.browser_manager.interact(action, tab_id)
                
                results.append(result)
                if not result.success:
                    success = False
                    error = result.error
                    break
                    
        except Exception as e:
            success = False
            error = str(e)
            logger.error(f"Script execution error: {error}")
            
        end_time = datetime.utcnow()
        
        return AutomationResult(
            script_id=script.id,
            success=success,
            start_time=start_time,
            end_time=end_time,
            results=results,
            error=error
        )
